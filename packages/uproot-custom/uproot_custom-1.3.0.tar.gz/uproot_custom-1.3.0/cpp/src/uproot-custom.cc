#include <pybind11/gil.h>
#include <pybind11/pybind11.h>
#include <vector>

#include "uproot-custom/uproot-custom.hh"

#ifdef UPROOT_DEBUG
#    define PRINT_BUFFER( buffer )                                                            \
        {                                                                                     \
            std::cout << "[DEBUG] ";                                                          \
            for ( int i = 0; i < 80; i++ )                                                    \
            { std::cout << (int)( buffer.get_cursor()[i] ) << " "; }                          \
            std::cout << std::endl;                                                           \
        }

#    define PRINT_MSG( msg )                                                                  \
        { std::cout << "[DEBUG] " << msg << std::endl; }

#    include <iostream>
#else
#    define PRINT_BUFFER( buffer )
#    define PRINT_MSG( msg )
#endif

namespace uproot {
    template <typename T>
    using SharedVector = std::shared_ptr<std::vector<T>>;

    template <typename T>
    class BasicTypeReader : public IElementReader {
      public:
        BasicTypeReader( std::string name )
            : IElementReader( name ), m_data( std::make_shared<std::vector<T>>() ) {}

        void read( BinaryBuffer& buffer ) override { m_data->push_back( buffer.read<T>() ); }

        py::object data() const override { return make_array( m_data ); }

      private:
        SharedVector<T> m_data;
    };

    template <>
    class BasicTypeReader<bool> : public IElementReader {
      public:
        BasicTypeReader( std::string name )
            : IElementReader( name ), m_data( std::make_shared<std::vector<uint8_t>>() ) {}

        void read( BinaryBuffer& buffer ) override {
            m_data->push_back( buffer.read<uint8_t>() != 0 );
        }

        py::object data() const override { return make_array( m_data ); }

      private:
        SharedVector<uint8_t> m_data;
    };

    /*
    -----------------------------------------------------------------------------
    -----------------------------------------------------------------------------
    -----------------------------------------------------------------------------
    */

    class TObjectReader : public IElementReader {

      public:
        TObjectReader( std::string name, bool keep_data )
            : IElementReader( name )
            , m_keep_data( keep_data )
            , m_unique_id( std::make_shared<std::vector<int32_t>>() )
            , m_bits( std::make_shared<std::vector<uint32_t>>() )
            , m_pidf( std::make_shared<std::vector<uint16_t>>() )
            , m_pidf_offsets( std::make_shared<std::vector<uint32_t>>( 1, 0 ) ) {}

        void read( BinaryBuffer& buffer ) override {
            buffer.skip_fVersion();

            auto fUniqueID = buffer.read<int32_t>();
            auto fBits     = buffer.read<uint32_t>();

            if ( fBits & ( BinaryBuffer::kIsReferenced ) )
            {
                if ( m_keep_data ) m_pidf->push_back( buffer.read<uint16_t>() );
                else buffer.skip( 2 );
            }

            if ( m_keep_data )
            {
                m_unique_id->push_back( fUniqueID );
                m_bits->push_back( fBits );
                m_pidf_offsets->push_back( m_pidf->size() );
            }
        }

        py::object data() const override {
            if ( !m_keep_data ) return py::none();

            auto unique_id_array = make_array( m_unique_id );
            auto bits_array      = make_array( m_bits );
            auto pidf_array      = make_array( m_pidf );
            auto pidf_offsets    = make_array( m_pidf_offsets );
            return py::make_tuple( unique_id_array, bits_array, pidf_array, pidf_offsets );
        }

      private:
        const bool m_keep_data;
        SharedVector<int32_t> m_unique_id;
        SharedVector<uint32_t> m_bits;
        SharedVector<uint16_t> m_pidf;
        SharedVector<uint32_t> m_pidf_offsets;
    };

    /*
    -----------------------------------------------------------------------------
    -----------------------------------------------------------------------------
    -----------------------------------------------------------------------------
    */

    class TStringReader : public IElementReader {
      public:
        TStringReader( std::string name )
            : IElementReader( name )
            , m_data( std::make_shared<std::vector<uint8_t>>() )
            , m_offsets( std::make_shared<std::vector<uint32_t>>( 1, 0 ) ) {}

        void read( BinaryBuffer& buffer ) override {
            uint32_t fSize = buffer.read<uint8_t>();
            if ( fSize == 255 ) fSize = buffer.read<uint32_t>();

            for ( int i = 0; i < fSize; i++ ) { m_data->push_back( buffer.read<uint8_t>() ); }
            m_offsets->push_back( m_data->size() );
        }

        py::object data() const override {
            auto offsets_array = make_array( m_offsets );
            auto data_array    = make_array( m_data );
            return py::make_tuple( offsets_array, data_array );
        }

      private:
        SharedVector<uint8_t> m_data;
        SharedVector<uint32_t> m_offsets;
    };

    /*
    -----------------------------------------------------------------------------
    -----------------------------------------------------------------------------
    -----------------------------------------------------------------------------
    */

    class STLSeqReader : public IElementReader {
      public:
        STLSeqReader( std::string name, bool with_header, SharedReader element_reader )
            : IElementReader( name )
            , m_with_header( with_header )
            , m_element_reader( element_reader )
            , m_offsets( std::make_shared<std::vector<uint32_t>>( 1, 0 ) ) {}

        void read( BinaryBuffer& buffer ) override {
            if ( m_with_header )
            {
                buffer.read_fNBytes();
                buffer.read_fVersion();
            }

            auto fSize = buffer.read<uint32_t>();
            m_offsets->push_back( m_offsets->back() + fSize );
            for ( auto i = 0; i < fSize; i++ ) m_element_reader->read( buffer );
        }

        py::object data() const override {
            auto offsets_array = make_array( m_offsets );
            auto elements_data = m_element_reader->data();
            return py::make_tuple( offsets_array, elements_data );
        }

      private:
        const bool m_with_header;
        SharedReader m_element_reader;
        SharedVector<uint32_t> m_offsets;
    };

    class STLMapReader : public IElementReader {
      public:
        STLMapReader( std::string name, bool with_header, SharedReader key_reader,
                      SharedReader value_reader )
            : IElementReader( name )
            , m_with_header( with_header )
            , m_offsets( std::make_shared<std::vector<uint32_t>>( 1, 0 ) )
            , m_key_reader( key_reader )
            , m_value_reader( value_reader ) {}

        void read( BinaryBuffer& buffer ) override {
            if ( m_with_header )
            {
                buffer.read_fNBytes();
                buffer.skip( 8 );
            }

            auto fSize = buffer.read<uint32_t>();
            m_offsets->push_back( m_offsets->back() + fSize );

            if ( m_with_header )
            {
                for ( auto i = 0; i < fSize; i++ ) m_key_reader->read( buffer );
                for ( auto i = 0; i < fSize; i++ ) m_value_reader->read( buffer );
            }
            else
            {
                for ( auto i = 0; i < fSize; i++ )
                {
                    m_key_reader->read( buffer );
                    m_value_reader->read( buffer );
                }
            }
        }

        py::object data() const override {
            auto offsets_array     = make_array( m_offsets );
            py::object keys_data   = m_key_reader->data();
            py::object values_data = m_value_reader->data();
            return py::make_tuple( offsets_array, keys_data, values_data );
        }

      private:
        const bool m_with_header;

        SharedVector<uint32_t> m_offsets;
        SharedReader m_key_reader;
        SharedReader m_value_reader;
    };

    class STLStringReader : public IElementReader {
      public:
        STLStringReader( std::string name, bool with_header )
            : IElementReader( name )
            , m_with_header( with_header )
            , m_offsets( std::make_shared<std::vector<uint32_t>>( 1, 0 ) )
            , m_data( std::make_shared<std::vector<uint8_t>>() ) {}

        void read( BinaryBuffer& buffer ) override {
            if ( m_with_header )
            {
                buffer.read_fNBytes();
                buffer.read_fVersion();
            }

            uint32_t fSize = buffer.read<uint8_t>();
            if ( fSize == 255 ) fSize = buffer.read<uint32_t>();

            m_offsets->push_back( m_offsets->back() + fSize );
            for ( int i = 0; i < fSize; i++ ) { m_data->push_back( buffer.read<uint8_t>() ); }
        }

        py::object data() const override {
            auto offsets_array = make_array( m_offsets );
            auto data_array    = make_array( m_data );

            return py::make_tuple( offsets_array, data_array );
        }

      private:
        const bool m_with_header;

        SharedVector<uint32_t> m_offsets;
        SharedVector<uint8_t> m_data;
    };

    /*
    -----------------------------------------------------------------------------
    -----------------------------------------------------------------------------
    -----------------------------------------------------------------------------
    */

    template <typename T>
    class TArrayReader : public IElementReader {
      public:
        TArrayReader( std::string name )
            : IElementReader( name )
            , m_offsets( std::make_shared<std::vector<uint32_t>>( 1, 0 ) )
            , m_data( std::make_shared<std::vector<T>>() ) {}

        void read( BinaryBuffer& buffer ) override {
            auto fSize = buffer.read<uint32_t>();
            m_offsets->push_back( m_offsets->back() + fSize );
            for ( auto i = 0; i < fSize; i++ ) { m_data->push_back( buffer.read<T>() ); }
        }

        py::object data() const override {
            auto offsets_array = make_array( m_offsets );
            auto data_array    = make_array( m_data );
            return py::make_tuple( offsets_array, data_array );
        }

      private:
        SharedVector<uint32_t> m_offsets;
        SharedVector<T> m_data;
    };

    /*
    -----------------------------------------------------------------------------
    -----------------------------------------------------------------------------
    -----------------------------------------------------------------------------
    */

    class BaseObjectReader : public IElementReader {
      public:
        BaseObjectReader( std::string name, std::vector<SharedReader> element_readers )
            : IElementReader( name ), m_element_readers( element_readers ) {}

        void read( BinaryBuffer& buffer ) override {
#ifdef UPROOT_DEBUG
            std::cout << "BaseObjectReader " << m_name << "::read(): " << std::endl;
            for ( int i = 0; i < 40; i++ ) std::cout << (int)buffer.get_cursor()[i] << " ";
            std::cout << std::endl << std::endl;
#endif
            buffer.read_fNBytes();
            buffer.read_fVersion();
            for ( auto& reader : m_element_readers )
            {
#ifdef UPROOT_DEBUG
                std::cout << "BaseObjectReader " << m_name << ": " << reader->name() << ":"
                          << std::endl;
                for ( int i = 0; i < 40; i++ ) std::cout << (int)buffer.get_cursor()[i] << " ";
                std::cout << std::endl << std::endl;
#endif
                reader->read( buffer );
            }
        }

        py::object data() const override {
            py::list res;
            for ( auto& reader : m_element_readers ) { res.append( reader->data() ); }
            return res;
        }

      private:
        std::vector<SharedReader> m_element_readers;
    };

    /*
    -----------------------------------------------------------------------------
    -----------------------------------------------------------------------------
    -----------------------------------------------------------------------------
    */

    class ObjectHeaderReader : public IElementReader {
      public:
        ObjectHeaderReader( std::string name, std::vector<SharedReader> element_readers )
            : IElementReader( name ), m_element_readers( element_readers ) {}

        void read( BinaryBuffer& buffer ) override {
            buffer.read_fNBytes();
            auto fTag = buffer.read<int32_t>();
            if ( fTag == -1 ) buffer.read_null_terminated_string();

            buffer.skip_fNBytes();
            buffer.skip_fVersion();
            for ( auto& reader : m_element_readers ) { reader->read( buffer ); }
        }

        py::object data() const override {
            py::list res;
            for ( auto& reader : m_element_readers ) { res.append( reader->data() ); }
            return res;
        }

      private:
        std::vector<SharedReader> m_element_readers;
    };

    /*
    -----------------------------------------------------------------------------
    -----------------------------------------------------------------------------
    -----------------------------------------------------------------------------
    */

    class CArrayReader : public IElementReader {
      public:
        CArrayReader( std::string name, bool is_obj, bool is_stdmap, const int64_t flat_size,
                      SharedReader element_reader )
            : IElementReader( name )
            , m_is_obj( is_obj )
            , m_is_stdmap( is_stdmap )
            , m_flat_size( flat_size )
            , m_offsets( std::make_shared<std::vector<uint32_t>>( 1, 0 ) )
            , m_element_reader( element_reader ) {}

        void read( BinaryBuffer& buffer ) override {

            PRINT_MSG( "CArrayReader::read() for " + m_name +
                       " with flat_size = " + std::to_string( m_flat_size ) +
                       ", is_obj = " + std::to_string( m_is_obj ) );
            PRINT_BUFFER( buffer );

            if ( m_flat_size > 0 )
            {
                if ( m_is_obj )
                {
                    buffer.read_fNBytes();
                    buffer.read_fVersion();
                    if ( m_is_stdmap ) buffer.skip( 6 );
                }

                for ( auto i = 0; i < m_flat_size; i++ )
                {
                    PRINT_MSG( "CArrayReader::read() reading element " + std::to_string( i ) );
                    PRINT_BUFFER( buffer );
                    m_element_reader->read( buffer );
                }
                PRINT_MSG( "" );
                PRINT_MSG( "" );
            }

            else
            {
                // get end-position
                auto n_entries     = buffer.entries();
                auto start_pos     = buffer.get_data();
                auto entry_offsets = buffer.get_offsets();
                auto cursor_pos    = buffer.get_cursor();
                auto entry_end = std::find_if( entry_offsets, entry_offsets + n_entries + 1,
                                               [start_pos, cursor_pos]( uint32_t offset ) {
                                                   return start_pos + offset > cursor_pos;
                                               } );

                PRINT_MSG( "CArrayReader::read() cursor_pos = " +
                           std::to_string( cursor_pos - start_pos ) +
                           "entry_end = " + std::to_string( *entry_end ) );

                if ( m_is_obj )
                {
                    buffer.read_fNBytes();
                    buffer.read_fVersion();
                    // if ( m_is_stdmap ) buffer.skip( 6 ); // Even std::map has no 6 bytes here.
                }

                uint32_t count = 0;
                while ( buffer.get_cursor() < start_pos + *entry_end )
                {

                    PRINT_MSG( "CArrayReader::read() reading element " +
                               std::to_string( count ) );
                    PRINT_BUFFER( buffer );
                    m_element_reader->read( buffer );
                    count += 1;
                }

                PRINT_MSG( "" );
                PRINT_MSG( "" );

                m_offsets->push_back( m_offsets->back() + count );
            }
        }

        py::object data() const override {
            if ( m_flat_size > 0 ) return m_element_reader->data();
            else
            {
                auto offsets_array = make_array( m_offsets );
                auto elements_data = m_element_reader->data();
                return py::make_tuple( offsets_array, elements_data );
            }
        }

      private:
        bool m_is_obj;
        bool m_is_stdmap;
        const int64_t m_flat_size;
        SharedReader m_element_reader;
        SharedVector<uint32_t> m_offsets;
    };

    /*
    -----------------------------------------------------------------------------
    -----------------------------------------------------------------------------
    -----------------------------------------------------------------------------
    */

    class EmptyReader : public IElementReader {
      public:
        EmptyReader( std::string name ) : IElementReader( name ) {}

        void read( BinaryBuffer& ) override {}
        py::object data() const override { return py::none(); }
    };

    /*
    -----------------------------------------------------------------------------
    -----------------------------------------------------------------------------
    -----------------------------------------------------------------------------
    */

    py::object py_read_data( py::array_t<uint8_t> data, py::array_t<uint32_t> offsets,
                             SharedReader reader ) {
        BinaryBuffer buffer( data, offsets );
        for ( auto i_evt = 0; i_evt < buffer.entries(); i_evt++ ) { reader->read( buffer ); }
        return reader->data();
    }

    PYBIND11_MODULE( cpp, m ) {
        m.doc() = "C++ module for uproot-custom";

        m.def( "read_data", &py_read_data, "Read data from a binary buffer", py::arg( "data" ),
               py::arg( "offsets" ), py::arg( "reader" ) );

        py::class_<IElementReader, SharedReader>( m, "IElementReader" )
            .def( "name", &IElementReader::name, "Get the name of the reader" );

        // Basic type readers
        register_reader<BasicTypeReader<uint8_t>>( m, "UInt8Reader" );
        register_reader<BasicTypeReader<uint16_t>>( m, "UInt16Reader" );
        register_reader<BasicTypeReader<uint32_t>>( m, "UInt32Reader" );
        register_reader<BasicTypeReader<uint64_t>>( m, "UInt64Reader" );
        register_reader<BasicTypeReader<int8_t>>( m, "Int8Reader" );
        register_reader<BasicTypeReader<int16_t>>( m, "Int16Reader" );
        register_reader<BasicTypeReader<int32_t>>( m, "Int32Reader" );
        register_reader<BasicTypeReader<int64_t>>( m, "Int64Reader" );
        register_reader<BasicTypeReader<float>>( m, "FloatReader" );
        register_reader<BasicTypeReader<double>>( m, "DoubleReader" );
        register_reader<BasicTypeReader<bool>>( m, "BoolReader" );

        // STL readers
        register_reader<STLSeqReader, bool, SharedReader>( m, "STLSeqReader" );
        register_reader<STLMapReader, bool, SharedReader, SharedReader>( m, "STLMapReader" );
        register_reader<STLStringReader, bool>( m, "STLStringReader" );

        // TArrayReader
        register_reader<TArrayReader<int8_t>>( m, "TArrayCReader" );
        register_reader<TArrayReader<int16_t>>( m, "TArraySReader" );
        register_reader<TArrayReader<int32_t>>( m, "TArrayIReader" );
        register_reader<TArrayReader<int64_t>>( m, "TArrayLReader" );
        register_reader<TArrayReader<float>>( m, "TArrayFReader" );
        register_reader<TArrayReader<double>>( m, "TArrayDReader" );

        // Other readers
        register_reader<TStringReader>( m, "TStringReader" );
        register_reader<TObjectReader, bool>( m, "TObjectReader" );
        register_reader<BaseObjectReader, std::vector<SharedReader>>( m, "BaseObjectReader" );
        register_reader<ObjectHeaderReader, std::vector<SharedReader>>( m,
                                                                        "ObjectHeaderReader" );
        register_reader<CArrayReader, bool, bool, int64_t, SharedReader>( m, "CArrayReader" );
        register_reader<EmptyReader>( m, "EmptyReader" );
    }

} // namespace uproot
