from .exceptions import *
import os
import sys


version = (0, 1, 3)
__version__ = "0.1.3"


class PackConfig:
    """
    Config object for pack_ctrl.options

    :param bool p_shortcuts:
        If true, pack dicts, tuples, lists without calling from_obj(...).
        Object types: {...} => None; (...) => None; [...] => False
        (default: True)

    :param bool sort_keys:
        Sort output dictionaries by key. (default: False)

    :param bool p_str_keys:
        If true, accept only strings as dict keys. (default: False)

    :param bool use_single_float:
        Use single precision float type for float. (default: False)
    """

    def __init__(self, p_shortcuts=True, sort_keys=False, p_str_keys=False,
                 use_single_float=False):
        self.p_shortcuts      = p_shortcuts
        self.sort_keys        = sort_keys
        self.p_str_keys       = p_str_keys
        self.use_single_float = use_single_float

class UnpackConfig:
    """
    Config object for unpack_ctrl.options

    :param bool u_shortcuts:
        If true, unpack dicts, tuples, lists without calling from_dict/list(...)
        Object types: None => {...}/(...), False => [...]
        (default: True)

    :param bool u_str_keys:
        If true, accept only strings as dict keys. (default: False)

    :param int read_size:
        Used as `file_like.read(read_size)`. (default: `min(16*1024, max_buffer_size)`)

    :param int max_buffer_size:
        (default: 100*1024*1024 (100MiB))
        Limits size of data waiting unpacked.  0 means 2**32-1.
        Raises `BufferFull` exception when it is insufficient.
        You should set this parameter when unpacking data from untrusted source.

    :param int max_str_len:
        Limits max length of str. (default: max_buffer_size)

    :param int max_bin_len:
        Limits max length of bin. (default: max_buffer_size)

    :param int max_list_len:
        Limits max length of list.
        (default: max_buffer_size)

    :param int max_dict_len:
        Limits max length of dict.
        (default: max_buffer_size//2)
    """

    def __init__(self, u_shortcuts=True, u_str_keys=False,
                 read_size=16*1024, max_buffer_size=0,
                 max_str_len=-1, max_bin_len=-1, max_list_len=-1, max_dict_len=-1):
        self.u_shortcuts  = u_shortcuts
        self.u_str_keys   = u_str_keys

        if max_buffer_size == 0: max_buffer_size = 2**32-1
        self.max_buffer_size = max_buffer_size
        self.read_size       = min(read_size, max_buffer_size)

        if max_str_len == -1:  max_str_len  = max_buffer_size
        if max_bin_len == -1:  max_bin_len  = max_buffer_size
        if max_list_len == -1: max_list_len = max_buffer_size
        if max_dict_len == -1: max_dict_len  = max_buffer_size//2

        self.max_str_len  = max_str_len
        self.max_bin_len  = max_bin_len
        self.max_list_len = max_list_len
        self.max_dict_len = max_dict_len


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

    See :class:`Packer` for options.
    """
    packer = Packer(pack_ctrl=pack_ctrl)
    stream.write(packer.pack(o))


def packb(o, pack_ctrl):
    """
    Pack object `o` and return packed bytes

    See :class:`Packer` for options.
    """
    return Packer(pack_ctrl=pack_ctrl).pack(o)


def unpack(stream, unpack_ctrl):
    """
    Unpack an object from `stream`.

    Raises `ExtraData` when `stream` contains extra bytes.
    See :class:`Unpacker` for options.
    """
    data = stream.read()
    return unpackb(data, unpack_ctrl=unpack_ctrl)


