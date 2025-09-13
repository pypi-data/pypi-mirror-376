#!/usr/bin/env python
from contexts_for_tests import pctrl, uctrl
from pytest import raises
from tmsgpack import packb, unpackb, Unpacker, FormatError, StackError, OutOfData


def test_invalidvalue():
    incomplete = b"\xd9\x97#DL_"  # str8 - length=0x97
    with raises(ValueError):
        unpackb(incomplete, unpack_ctrl=uctrl())

    with raises(OutOfData):
        unpacker = Unpacker(unpack_ctrl=uctrl())
        unpacker.feed(incomplete)
        unpacker.unpack()

    with raises(FormatError):
        unpackb(b"\xc1", unpack_ctrl=uctrl())  # (undefined tag)

    with raises(FormatError):
        unpackb(b"\x91\xc1", unpack_ctrl=uctrl())  # fixlist(len=1) [ (undefined tag) ]

    with raises(StackError):
        unpackb(b"\x91" * 3000, unpack_ctrl=uctrl())  # nested fixlist(len=1)


def test_p_str_keys():
    packb({1:2}, pack_ctrl=pctrl())
    with raises(ValueError):
        packb({1:2}, pack_ctrl=pctrl(p_str_keys=True))

def test_u_str_keys():
    valid = {"unicode": 1}
    packed = packb(valid, pack_ctrl=pctrl())
    assert valid == unpackb(packed, unpack_ctrl=uctrl(u_str_keys=True))

    invalid = {b"binary": 1}
    packed = packb(invalid, pack_ctrl=pctrl())
    with raises(ValueError):
        unpackb(packed, unpack_ctrl=uctrl(u_str_keys=True))

    invalid = {42: 1}
    packed = packb(invalid, pack_ctrl=pctrl())
    with raises(ValueError):
        unpackb(packed, unpack_ctrl=uctrl(u_str_keys=True))

