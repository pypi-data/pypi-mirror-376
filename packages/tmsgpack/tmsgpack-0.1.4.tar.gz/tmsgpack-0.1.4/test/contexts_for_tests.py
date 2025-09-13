from tmsgpack import PackOptions, UnpackOptions
from dataclasses import dataclass

@dataclass
class TestPackCtrl:
    def from_obj(self, obj):
        raise TypeError(f'Cannot serialize {type(obj)} object.')
    options: PackOptions

@dataclass
class TestUnpackCtrl:
    def from_dict(self, ctype, dct):
        raise ValueError(f'Unpack type not supported: {ctype} data: {dct}')
    def from_tuple(self, ctype, lst):
        raise ValueError(f'Unpack type not supported: {ctype} data: {lst}')
    options: UnpackOptions

def pctrl(**kwargs): return TestPackCtrl(options=PackOptions(**kwargs))
def uctrl(**kwargs): return TestUnpackCtrl(options=UnpackOptions(**kwargs))
