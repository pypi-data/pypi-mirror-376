from .exceptions import *
import os
import sys
from dataclasses import dataclass

version = (0, 1, 4)
__version__ = "0.1.4"


@dataclass
class PackOptions:
    """
    Config object for pack_ctrl.options
    """

    # If true, pack dicts, tuples, lists without calling from_obj(...).
    # Object types: {...} => None; (...) => None; [...] => False
    p_shortcuts: bool = True

    # Sort output dictionaries by key.
    sort_keys: bool = False

    # If true, accept only strings as dict keys.
    p_str_keys: bool = False

    # Use single precision float type for float.
    use_single_float: bool = False

    def _packb(self, data, pack_ctrl): return packb(data, pack_ctrl=pack_ctrl)

@dataclass
class UnpackOptions:
    """
    Config object for unpack_ctrl.options
    """

    # If true, unpack dicts, tuples, lists without calling from_dict/list(...)
    # Object types: None => {...}/(...), False => [...]
    u_shortcuts: bool = True

    # If true, accept only strings as dict keys.
    u_str_keys: bool = False

    # Used as `file_like.read(read_size)`.
    read_size: int = 16*1024

    # Limits size of data waiting unpacked.
    # Raises `BufferFull` exception when it is insufficient.
    # You should set this parameter when unpacking data from untrusted source.
    max_buffer_size: int = 0  # 0 means: 2**32-1

    # Limits max length of str. (default: max_buffer_size)
    max_str_len: int = -1  # -1 means max_buffer_size

    # Limits max length of bin.
    max_bin_len: int = -1  # -1 means max_buffer_size

    # Limits max length of list.
    max_list_len: int = -1  # -1 means max_buffer_size

    # Limits max length of dict.
    max_dict_len: int = -1  # -1 means max_buffer_size//2


    def __post_init__(self): self._init_unpack_config()

    def _init_unpack_config(self):
        if self.max_buffer_size == 0: self.max_buffer_size = 2**32-1
        self.read_size = min(self.read_size, self.max_buffer_size)

        if self.max_str_len == -1:  self.max_str_len  = self.max_buffer_size
        if self.max_bin_len == -1:  self.max_bin_len  = self.max_buffer_size
        if self.max_list_len == -1: self.max_list_len = self.max_buffer_size
        if self.max_dict_len == -1: self.max_dict_len = self.max_buffer_size//2

    def _unpackb(self, data, unpack_ctrl): return unpackb(data, unpack_ctrl=unpack_ctrl)

@dataclass
class PackUnpackOptions(PackOptions, UnpackOptions):
    def __post_init__(self): self._init_unpack_config()


if os.environ.get("TMSGPACK_PUREPYTHON"):
    from .fallback import Packer, unpackb, Unpacker
else:
    try:
        from ._ctmsgpack import Packer, unpackb, Unpacker
    except ImportError:
        from .fallback import Packer, unpackb, Unpacker


def pack(o, stream, pack_ctrl):
    """
    Pack object `o` and write it to `stream`

    See :class:`PackOptions`.
    """
    packer = Packer(pack_ctrl=pack_ctrl)
    stream.write(packer.pack(o))


def packb(o, pack_ctrl):
    """
    Pack object `o` and return packed bytes

    See :class:`PackOptions`.
    """
    return Packer(pack_ctrl=pack_ctrl).pack(o)


def unpack(stream, unpack_ctrl):
    """
    Unpack an object from `stream`.

    Raises `ExtraData` when `stream` contains extra bytes.
    See :class:`UnpackOptions`.
    """
    data = stream.read()
    return unpackb(data, unpack_ctrl=unpack_ctrl)


