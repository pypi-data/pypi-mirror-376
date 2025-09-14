from __future__ import annotations

from typing import Union

import awkward as ak
import awkward.contents
import awkward.index
import numpy as np

import uproot_custom.cpp
from uproot_custom.utils import (
    get_map_key_val_typenames,
    get_sequence_element_typename,
    get_top_type_name,
)

registered_readers: set[type["BaseReader"]] = set()


def gen_tree_config(
    cls_streamer_info: dict,
    all_streamer_info: dict,
    item_path: str = "",
    called_from_top: bool = False,
) -> dict:
    """
    Generate reader configuration for a class streamer information.

    The content it returns should be:

    ```python
    {
        "reader": ReaderType,
        "name": str,
        "ctype": str, # for CTypeReader, TArrayReader
        "element_reader": dict, # reader config of the element, for STLVectorReader, SimpleCArrayReader, TObjectCArrayReader
        "flat_size": int, # for SimpleCArrayReader, TObjectCArrayReader
        "fMaxIndex": list[int], # for SimpleCArrayReader, TObjectCArrayReader
        "fArrayDim": int, # for SimpleCArrayReader, TObjectCArrayReader
        "key_reader": dict, # reader config of the key, for STLMapReader
        "val_reader": dict, # reader config of the value, for STLMapReader
        "sub_readers": list[dict], # for ObjectReader, ObjectHeaderReader
        "is_top_level": bool, # for STLVectorReader, STLMapReader, STLStringReader
    }
    ```

    Args:
        cls_streamer_info (dict): Class streamer information.
        all_streamer_info (dict): All streamer information.
        item_path (str): Path to the item.

    Returns:
        dict: Reader configuration.
    """
    fName = cls_streamer_info["fName"]

    top_type_name = (
        get_top_type_name(cls_streamer_info["fTypeName"])
        if "fTypeName" in cls_streamer_info
        else None
    )

    if not called_from_top:
        item_path = f"{item_path}.{fName}"

    for reader in sorted(registered_readers, key=lambda x: x.priority(), reverse=True):
        tree_config = reader.gen_tree_config(
            top_type_name,
            cls_streamer_info,
            all_streamer_info,
            item_path,
            called_from_top=called_from_top,
        )
        if tree_config is not None:
            return tree_config

    raise ValueError(f"Unknown type: {cls_streamer_info['fTypeName']} for {item_path}")


def get_cpp_reader(tree_config: dict):
    for reader in sorted(registered_readers, key=lambda x: x.priority(), reverse=True):
        cpp_reader = reader.get_cpp_reader(tree_config)
        if cpp_reader is not None:
            return cpp_reader

    raise ValueError(f"Unknown reader type: {tree_config['reader']} for {tree_config['name']}")


def reconstruct_array(
    raw_data: Union[np.ndarray, tuple, list, None],
    tree_config: dict,
) -> Union[ak.Array, None]:
    for reader in sorted(registered_readers, key=lambda x: x.priority(), reverse=True):
        data = reader.reconstruct_array(raw_data, tree_config)
        if data is not None:
            return data

    raise ValueError(f"Unknown reader type: {tree_config['reader']} for {tree_config['name']}")


def read_branch(
    data: np.ndarray[np.uint8],
    offsets: np.ndarray,
    cls_streamer_info: dict,
    all_streamer_info: dict[str, list[dict]],
    item_path: str = "",
):
    tree_config = gen_tree_config(
        cls_streamer_info,
        all_streamer_info,
        item_path,
        called_from_top=True,
    )
    reader = get_cpp_reader(tree_config)

    if offsets is None:
        nbyte = cls_streamer_info["fSize"]
        offsets = np.arange(data.size // nbyte + 1, dtype=np.uint32) * nbyte
    raw_data = uproot_custom.cpp.read_data(data, offsets, reader)

    return reconstruct_array(raw_data, tree_config)


class BaseReader:
    @classmethod
    def priority(cls) -> int:
        """
        Return the priority of the reader. Readers with higher priority will be called first.
        """
        return 10

    @classmethod
    def gen_tree_config(
        cls,
        cls_streamer_info: dict,
        all_streamer_info: dict,
        item_path: str = "",
        called_from_top: bool = False,
    ) -> dict:
        raise NotImplementedError("This method should be implemented in subclasses.")

    @classmethod
    def get_cpp_reader(cls, tree_config: dict) -> Union["BaseReader", None]:
        """
        Args:
            tree_config (dict): The configuration dictionary for the reader.

        Returns:
            BaseReader: An instance of the appropriate reader class.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")

    @classmethod
    def reconstruct_array(
        cls,
        raw_data: Union[np.ndarray, tuple, list, None],
        tree_config: dict,
    ) -> Union[ak.Array, None]:
        """
        Args:
            raw_data (Union[np.ndarray, tuple, list, None]): The raw data to be
                recovered.
            tree_config (dict): The configuration dictionary for the reader.

        Returns:
            ak.Array: The recovered data as an ak array.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")


class BasicTypeReader(BaseReader):
    typenames = {
        "bool": "bool",
        "char": "i1",
        "short": "i2",
        "int": "i4",
        "long": "i8",
        "long long": "i8",
        "unsigned char": "u1",
        "unsigned short": "u2",
        "unsigned int": "u4",
        "unsigned long": "u8",
        "unsigned long long": "u8",
        "float": "f",
        "double": "d",
        # cstdint
        "int8_t": "i1",
        "int16_t": "i2",
        "int32_t": "i4",
        "int64_t": "i8",
        "uint8_t": "u1",
        "uint16_t": "u2",
        "uint32_t": "u4",
        "uint64_t": "u8",
        # ROOT types
        "Bool_t": "bool",
        "Char_t": "i1",
        "Short_t": "i2",
        "Int_t": "i4",
        "Long_t": "i8",
        "UChar_t": "u1",
        "UShort_t": "u2",
        "UInt_t": "u4",
        "ULong_t": "u8",
        "Float_t": "f",
        "Double_t": "d",
    }

    cpp_reader_map = {
        "bool": uproot_custom.cpp.BoolReader,
        "i1": uproot_custom.cpp.Int8Reader,
        "i2": uproot_custom.cpp.Int16Reader,
        "i4": uproot_custom.cpp.Int32Reader,
        "i8": uproot_custom.cpp.Int64Reader,
        "u1": uproot_custom.cpp.UInt8Reader,
        "u2": uproot_custom.cpp.UInt16Reader,
        "u4": uproot_custom.cpp.UInt32Reader,
        "u8": uproot_custom.cpp.UInt64Reader,
        "f": uproot_custom.cpp.FloatReader,
        "d": uproot_custom.cpp.DoubleReader,
    }

    @classmethod
    def gen_tree_config(
        cls,
        top_type_name,
        cls_streamer_info,
        all_streamer_info,
        item_path,
        called_from_top,
    ):
        if top_type_name in BasicTypeReader.typenames:
            ctype = BasicTypeReader.typenames[top_type_name]
            return {
                "reader": cls,
                "name": cls_streamer_info["fName"],
                "ctype": ctype,
            }
        else:
            return None

    @classmethod
    def get_cpp_reader(cls, tree_config: dict):
        if tree_config["reader"] is not cls:
            return None

        ctype = tree_config["ctype"]
        return cls.cpp_reader_map[ctype](tree_config["name"])

    @classmethod
    def reconstruct_array(cls, raw_data, tree_config):
        if tree_config["reader"] is not cls:
            return None

        if tree_config["ctype"] == "bool":
            raw_data = raw_data.astype(np.bool_)
        return ak.contents.NumpyArray(raw_data)


stl_typenames = {
    "vector",
    "array",
    "map",
    "unordered_map",
    "string",
    "list",
    "set",
    "unordered_set",
}


class STLSeqReader(BaseReader):
    @classmethod
    def gen_tree_config(
        cls,
        top_type_name,
        cls_streamer_info,
        all_streamer_info,
        item_path,
        called_from_top,
    ):
        if top_type_name not in ["vector", "array", "list", "set", "unordered_set"]:
            return None

        fName = cls_streamer_info["fName"]
        fTypeName = cls_streamer_info["fTypeName"]
        element_type = get_sequence_element_typename(fTypeName)
        element_info = {
            "fName": fName,
            "fTypeName": element_type,
        }

        element_tree_config = gen_tree_config(
            element_info,
            all_streamer_info,
            item_path,
        )

        top_element_type = get_top_type_name(element_type)
        if top_element_type in stl_typenames:
            element_tree_config["with_header"] = False

        return {
            "reader": cls,
            "name": fName,
            "element_reader": element_tree_config,
        }

    @classmethod
    def get_cpp_reader(cls, tree_config: dict):
        if tree_config["reader"] is not cls:
            return None

        element_cpp_reader = get_cpp_reader(tree_config["element_reader"])
        with_header = tree_config.get("with_header", True)
        return uproot_custom.cpp.STLSeqReader(
            tree_config["name"],
            with_header,
            element_cpp_reader,
        )

    @classmethod
    def reconstruct_array(cls, raw_data, tree_config):
        if tree_config["reader"] is not cls:
            return None

        offsets, element_raw_data = raw_data
        element_data = reconstruct_array(
            element_raw_data,
            tree_config["element_reader"],
        )

        return ak.contents.ListOffsetArray(
            ak.index.Index64(offsets),
            element_data,
        )


class STLMapReader(BaseReader):
    """
    This class reads std::map from a binary parser.
    """

    @classmethod
    def gen_tree_config(
        cls,
        top_type_name,
        cls_streamer_info,
        all_streamer_info,
        item_path,
        called_from_top,
    ):
        if top_type_name not in ["map", "unordered_map", "multimap"]:
            return None

        fTypeName = cls_streamer_info["fTypeName"]
        key_type_name, val_type_name = get_map_key_val_typenames(fTypeName)

        fName = cls_streamer_info["fName"]
        key_info = {
            "fName": "key",
            "fTypeName": key_type_name,
        }

        val_info = {
            "fName": "val",
            "fTypeName": val_type_name,
        }

        key_tree_config = gen_tree_config(key_info, all_streamer_info, item_path)
        if get_top_type_name(key_type_name) in stl_typenames:
            key_tree_config["with_header"] = False

        val_tree_config = gen_tree_config(val_info, all_streamer_info, item_path)
        if get_top_type_name(val_type_name) in stl_typenames:
            val_tree_config["with_header"] = False

        return {
            "reader": cls,
            "name": fName,
            "key_reader": key_tree_config,
            "val_reader": val_tree_config,
        }

    @classmethod
    def get_cpp_reader(cls, tree_config: dict):
        if tree_config["reader"] is not cls:
            return None

        key_cpp_reader = get_cpp_reader(tree_config["key_reader"])
        val_cpp_reader = get_cpp_reader(tree_config["val_reader"])
        with_header = tree_config.get("with_header", True)
        return uproot_custom.cpp.STLMapReader(
            tree_config["name"],
            with_header,
            key_cpp_reader,
            val_cpp_reader,
        )

    @classmethod
    def reconstruct_array(cls, raw_data, tree_config):
        if tree_config["reader"] is not cls:
            return None

        key_tree_config = tree_config["key_reader"]
        val_tree_config = tree_config["val_reader"]
        offsets, key_raw_data, val_raw_data = raw_data
        key_data = reconstruct_array(key_raw_data, key_tree_config)
        val_data = reconstruct_array(val_raw_data, val_tree_config)

        return ak.contents.ListOffsetArray(
            ak.index.Index64(offsets),
            ak.contents.RecordArray(
                [key_data, val_data],
                [key_tree_config["name"], val_tree_config["name"]],
            ),
        )


class STLStringReader(BaseReader):
    """
    This class reads std::string from a binary parser.
    """

    @classmethod
    def gen_tree_config(
        cls,
        top_type_name,
        cls_streamer_info,
        all_streamer_info,
        item_path,
        called_from_top,
    ):
        if top_type_name != "string":
            return None

        return {
            "reader": cls,
            "name": cls_streamer_info["fName"],
            "with_header": not called_from_top,
        }

    @classmethod
    def get_cpp_reader(cls, tree_config: dict):
        if tree_config["reader"] is not cls:
            return None

        return uproot_custom.cpp.STLStringReader(
            tree_config["name"],
            tree_config.get("with_header", True),
        )

    @classmethod
    def reconstruct_array(cls, raw_data, tree_config):
        if tree_config["reader"] is not cls:
            return None

        offsets, data = raw_data
        return awkward.contents.ListOffsetArray(
            awkward.index.Index64(offsets),
            awkward.contents.NumpyArray(data, parameters={"__array__": "char"}),
            parameters={"__array__": "string"},
        )


class TArrayReader(BaseReader):
    """
    This class reads TArray from a binary paerser.

    TArray includes TArrayC, TArrayS, TArrayI, TArrayL, TArrayF, and TArrayD.
    Corresponding ctype is u1, u2, i4, i8, f, and d.
    """

    typenames = {
        "TArrayC": "i1",
        "TArrayS": "i2",
        "TArrayI": "i4",
        "TArrayL": "i8",
        "TArrayF": "f",
        "TArrayD": "d",
    }

    @classmethod
    def gen_tree_config(
        cls,
        top_type_name,
        cls_streamer_info,
        all_streamer_info,
        item_path,
        called_from_top,
    ):
        if top_type_name not in cls.typenames:
            return None

        ctype = cls.typenames[top_type_name]
        return {
            "reader": cls,
            "name": cls_streamer_info["fName"],
            "ctype": ctype,
        }

    @classmethod
    def get_cpp_reader(cls, tree_config: dict):
        if tree_config["reader"] is not cls:
            return None

        ctype = tree_config["ctype"]

        return {
            "i1": uproot_custom.cpp.TArrayCReader,
            "i2": uproot_custom.cpp.TArraySReader,
            "i4": uproot_custom.cpp.TArrayIReader,
            "i8": uproot_custom.cpp.TArrayLReader,
            "f": uproot_custom.cpp.TArrayFReader,
            "d": uproot_custom.cpp.TArrayDReader,
        }[ctype](tree_config["name"])

    @classmethod
    def reconstruct_array(cls, raw_data, tree_config):
        if tree_config["reader"] is not cls:
            return None

        offsets, data = raw_data
        return awkward.contents.ListOffsetArray(
            awkward.index.Index64(offsets),
            awkward.contents.NumpyArray(data),
        )


class TStringReader(BaseReader):
    """
    This class reads TString from a binary parser.
    """

    @classmethod
    def gen_tree_config(
        cls,
        top_type_name,
        cls_streamer_info,
        all_streamer_info,
        item_path,
        called_from_top,
    ):
        if top_type_name != "TString":
            return None

        return {
            "reader": cls,
            "name": cls_streamer_info["fName"],
        }

    @classmethod
    def get_cpp_reader(cls, tree_config: dict):
        if tree_config["reader"] is not cls:
            return None

        return uproot_custom.cpp.TStringReader(tree_config["name"])

    @classmethod
    def reconstruct_array(cls, raw_data, tree_config):
        if tree_config["reader"] is not cls:
            return None

        offsets, data = raw_data
        return awkward.contents.ListOffsetArray(
            awkward.index.Index64(offsets),
            awkward.contents.NumpyArray(data, parameters={"__array__": "char"}),
            parameters={"__array__": "string"},
        )


class TObjectReader(BaseReader):
    """
    This class reads TObject from a binary parser.

    It will not record any data.
    """

    # Whether keep TObject data.
    keep_data_itempaths: set[str] = set()

    @classmethod
    def gen_tree_config(
        cls,
        top_type_name,
        cls_streamer_info,
        all_streamer_info,
        item_path,
        called_from_top,
    ):
        if top_type_name != "BASE":
            return None

        fType = cls_streamer_info["fType"]
        if fType != 66:
            return None

        return {
            "reader": cls,
            "name": cls_streamer_info["fName"],
            "keep_data": item_path in cls.keep_data_itempaths,
        }

    @classmethod
    def get_cpp_reader(cls, tree_config: dict):
        if tree_config["reader"] is not cls:
            return None

        return uproot_custom.cpp.TObjectReader(
            tree_config["name"],
            tree_config["keep_data"],
        )

    @classmethod
    def reconstruct_array(cls, raw_data, tree_config):
        if tree_config["reader"] is not cls:
            return None

        if not tree_config["keep_data"]:
            return None

        unique_ids, bits, pidf, pidf_offsets = raw_data

        return awkward.contents.RecordArray(
            [
                awkward.contents.NumpyArray(unique_ids),
                awkward.contents.NumpyArray(bits),
                awkward.contents.ListOffsetArray(
                    awkward.index.Index64(pidf_offsets),
                    awkward.contents.NumpyArray(pidf),
                ),
            ],
            ["fUniqueID", "fBits", "pidf"],
        )


class CArrayReader(BaseReader):
    """
    This class reads a C-array from a binary parser.
    """

    @classmethod
    def priority(cls):
        return 20  # This reader should be called first

    @classmethod
    def gen_tree_config(
        cls,
        top_type_name,
        cls_streamer_info,
        all_streamer_info,
        item_path,
        called_from_top,
    ):
        fTypeName = cls_streamer_info.get("fTypeName", "")
        if not fTypeName.endswith("[]") and cls_streamer_info.get("fArrayDim", 0) == 0:
            return None

        fName = cls_streamer_info["fName"]

        if fTypeName.endswith("[]"):
            fArrayDim = -1
            fMaxIndex = -1
            flat_size = -1
        else:
            fArrayDim = cls_streamer_info["fArrayDim"]
            fMaxIndex = cls_streamer_info["fMaxIndex"]
            flat_size = np.prod(fMaxIndex[:fArrayDim])

        element_streamer_info = cls_streamer_info.copy()
        element_streamer_info["fArrayDim"] = 0
        while fTypeName.endswith("[]"):
            fTypeName = fTypeName[:-2]
        element_streamer_info["fTypeName"] = fTypeName

        element_tree_config = gen_tree_config(
            element_streamer_info,
            all_streamer_info,
        )

        assert flat_size != 0, f"flatten_size should cannot be 0."

        # c-type number or TArray
        top_type_name = get_top_type_name(fTypeName)
        if top_type_name in BasicTypeReader.typenames or fTypeName in TArrayReader.typenames:
            return {
                "reader": cls,
                "name": fName,
                "is_obj": False,
                "element_reader": element_tree_config,
                "flat_size": flat_size,
                "fMaxIndex": fMaxIndex,
                "fArrayDim": fArrayDim,
            }

        # TSTring
        elif top_type_name == "TString":
            return {
                "reader": cls,
                "name": fName,
                "is_obj": True,
                "element_reader": element_tree_config,
                "flat_size": flat_size,
                "fMaxIndex": fMaxIndex,
                "fArrayDim": fArrayDim,
            }

        # STL
        elif top_type_name in stl_typenames:
            element_tree_config["with_header"] = False

            is_obj = not called_from_top
            if cls_streamer_info.get("fType", 0) == 500:
                is_obj = True

            # when is a ragged array, vector/map will have a reader
            element_reader = element_tree_config.get("reader", None)
            if (
                flat_size < 0
                and element_reader is not None
                and element_reader != BasicTypeReader
            ):
                is_obj = True

            is_stdmap = top_type_name in ["map", "unordered_map", "multimap"]

            return {
                "reader": cls,
                "name": fName,
                "is_obj": is_obj,
                "is_stdmap": is_stdmap,
                "flat_size": flat_size,
                "element_reader": element_tree_config,
                "fMaxIndex": fMaxIndex,
                "fArrayDim": fArrayDim,
            }

        else:
            raise ValueError(f"Unknown type: {top_type_name} for C-array: {fTypeName}")

    @classmethod
    def get_cpp_reader(cls, tree_config: dict):
        reader_type = tree_config["reader"]
        if reader_type is not cls:
            return None

        element_reader = get_cpp_reader(tree_config["element_reader"])

        return uproot_custom.cpp.CArrayReader(
            tree_config["name"],
            tree_config["is_obj"],
            tree_config.get("is_stdmap", False),
            tree_config["flat_size"],
            element_reader,
        )

    @classmethod
    def reconstruct_array(cls, raw_data, tree_config):
        if tree_config["reader"] is not cls:
            return None

        element_tree_config = tree_config["element_reader"]
        flat_size = tree_config["flat_size"]

        if flat_size > 0:
            fMaxIndex = tree_config["fMaxIndex"]
            fArrayDim = tree_config["fArrayDim"]
            shape = [fMaxIndex[i] for i in range(fArrayDim)]

            element_data = reconstruct_array(
                raw_data,
                element_tree_config,
            )

            for s in shape[::-1]:
                element_data = awkward.contents.RegularArray(element_data, int(s))

            return element_data

        else:  # ragged array
            offsets, element_raw_data = raw_data
            element_data = reconstruct_array(
                element_raw_data,
                element_tree_config,
            )
            return ak.contents.ListOffsetArray(
                ak.index.Index64(offsets),
                element_data,
            )


class BaseObjectReader(BaseReader):
    """
    It has fNBytes(uint32), fVersion(uint16) at the beginning.
    """

    @classmethod
    def gen_tree_config(
        cls,
        top_type_name,
        cls_streamer_info,
        all_streamer_info,
        item_path,
        called_from_top,
    ):
        if top_type_name != "BASE":
            return None

        fType = cls_streamer_info["fType"]
        if fType != 0:
            return None

        fName = cls_streamer_info["fName"]
        sub_streamers: list = all_streamer_info[fName]

        sub_tree_configs = [
            gen_tree_config(s, all_streamer_info, item_path) for s in sub_streamers
        ]

        return {
            "reader": cls,
            "name": fName,
            "sub_readers": sub_tree_configs,
        }

    @classmethod
    def get_cpp_reader(cls, tree_config: dict):
        if tree_config["reader"] is not cls:
            return None

        sub_readers = [get_cpp_reader(s) for s in tree_config["sub_readers"]]
        return uproot_custom.cpp.BaseObjectReader(tree_config["name"], sub_readers)

    @classmethod
    def reconstruct_array(cls, raw_data, tree_config):
        if tree_config["reader"] is not cls:
            return None

        sub_tree_configs = tree_config["sub_readers"]

        arr_dict = {}
        for s_cfg, s_data in zip(sub_tree_configs, raw_data):
            if s_cfg["reader"] == TObjectReader and not s_cfg["keep_data"]:
                continue

            s_name = s_cfg["name"]
            arr_dict[s_name] = reconstruct_array(s_data, s_cfg)

        return awkward.contents.RecordArray(
            [arr_dict[k] for k in arr_dict],
            [k for k in arr_dict],
        )


class ObjectHeaderReader(BaseReader):
    """
    This class read an object starting with an object header.
    """

    @classmethod
    def priority(cls):
        return 0  # should be called last

    @classmethod
    def gen_tree_config(
        cls,
        top_type_name,
        cls_streamer_info,
        all_streamer_info,
        item_path,
        called_from_top,
    ):
        sub_streamers: list = all_streamer_info[top_type_name]
        sub_tree_configs = [
            gen_tree_config(s, all_streamer_info, item_path) for s in sub_streamers
        ]
        return {
            "reader": cls,
            "name": top_type_name,
            "sub_readers": sub_tree_configs,
        }

    @classmethod
    def get_cpp_reader(cls, tree_config: dict):
        if tree_config["reader"] is not cls:
            return None

        sub_readers = [get_cpp_reader(s) for s in tree_config["sub_readers"]]
        return uproot_custom.cpp.ObjectHeaderReader(tree_config["name"], sub_readers)

    @classmethod
    def reconstruct_array(cls, raw_data, tree_config):
        if tree_config["reader"] is not cls:
            return None

        sub_tree_configs = tree_config["sub_readers"]

        arr_dict = {}
        for s_cfg, s_data in zip(sub_tree_configs, raw_data):
            if s_cfg["reader"] == TObjectReader and not s_cfg["keep_data"]:
                continue

            s_name = s_cfg["name"]
            arr_dict[s_name] = reconstruct_array(s_data, s_cfg)

        return awkward.contents.RecordArray(
            [arr_dict[k] for k in arr_dict],
            [k for k in arr_dict],
        )


class EmptyReader(BaseReader):
    """
    This class does nothing.
    """

    @classmethod
    def gen_tree_config(
        cls,
        top_type_name,
        cls_streamer_info,
        all_streamer_info,
        item_path,
        called_from_top,
    ):
        return None

    @classmethod
    def get_cpp_reader(cls, tree_config: dict):
        if tree_config["reader"] is not cls:
            return None

        return uproot_custom.cpp.EmptyReader(tree_config["name"])

    @classmethod
    def reconstruct_array(cls, raw_data, tree_config):
        if tree_config["reader"] is not cls:
            return None

        return awkward.contents.EmptyArray()


registered_readers |= {
    BasicTypeReader,
    STLSeqReader,
    STLMapReader,
    STLStringReader,
    TArrayReader,
    TStringReader,
    TObjectReader,
    CArrayReader,
    BaseObjectReader,
    ObjectHeaderReader,
    EmptyReader,
}
