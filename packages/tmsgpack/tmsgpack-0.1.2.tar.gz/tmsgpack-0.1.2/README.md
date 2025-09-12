# tmsgpack: Typed MessagePack-inspired pack/unpack component

See also: [FORMAT.md](FORMAT.md) and [DEVELOP.md](DEVELOP.md)

The tmsgpack format expresses **typed objects**: maps and arrays (or: dicts and
tuples/lists) with an `object_type` property.

Unlike msgpack and pickle, this is not a batteries-included end-to-end serialization
solution.  It is a composable component that helps you to build end-to-end communication
solutions.

Your system solution design will make decisions on:
* What objects are serializable and what objects are not.
* What code to use (and, maybe, dynamically load) to instantiate serialized objects.
* How to represent objects that are unpacked but not supposed to 'live' in this process.
* How to share dynamic data between different packs/unpacks.
* How to asynchronously load and integrate shared data from different sources.
* How to map typed object meaning between different programming languages.
* Whether and how to convert persisted "old" data to current, new semantics (schemas).
* How much to attach explicit meaning and predictable schemas to your object types.
* Whether or not to use the 'expression execution' capabilities of tmsgpack.
* etc.

This python package makes a minimal (backwards-incompatible) modification to the
msgpack format to make all this elegantly possible.  This package is based on
`msgpack v1.0.5`.

## Installation
```bash
pip install tmsgpack
```

## Usage
Packing and unpacking data is controlled by `pack_ctrl` and `unpack_ctrl` objects (see
below for details how to create them):
```python
from tmsgpack import packb, unpackb
packed = packb(data, pack_ctrl=pack_ctrl)
unpacked = unpackb(packed, unpack_ctrl=unpack_ctrl)
```

## Streaming unpacking
For multiple uses, you can use packer and unpacker objects:
```python
from tmsgpack import Packer
packer = Packer(pack_ctrl=pack_ctrl)

packed = packer.pack(data) # Send these packages via a socket...

---
from tmsgpack import Packer, Unpacker

unpacker = Unpacker(unpack_ctrl=unpack_ctrl)
while buf := sock.recv(1024**2):
    unpacker.feed(buf)
    for o in unpacker:
        process(o)
```

## Minimal pack_ctrl and unpack_ctrl objects
Minimal controllers allow only JSON-like objects and raise errors when you ask for more
(below, we show examples for more useful controllers):
```python
from tmsgpack import PackConfig, UnpackConfig
from dataclasses import dataclass

@dataclass
class MinimalPackCtrl:
    def from_obj(self, obj):
        raise TypeError(f'Cannot serialize {type(obj)} object.')
    options: PackConfig

@dataclass
class MinimalUnpackCtrl:
    def from_dict(self, ctype, dct):
        raise ValueError(f'Unpack type not supported: {ctype} data: {dct}')
    def from_tuple(self, ctype, lst):
        raise ValueError(f'Unpack type not supported: {ctype} data: {lst}')
    options: UnpackConfig

def pctrl(**kwargs): return MinimalPackCtrl(options=PackConfig(**kwargs))
def uctrl(**kwargs): return MinimalUnpackCtrl(options=UnpackConfig(**kwargs))

minimal_pack_ctrl = pctrl()
minimal_unpack_ctrl = uctrl()
```

## The API and configuration
As you see, the `pack_ctrl` object provides a method `from_obj`. The `unpack_ctrl`
object provides the methods `from_dict` and `from_tuple`:
```python
as_dict, data_type, data = pack_ctrl.from(obj)

# When `as_dict` is true, then `data` should be a dictionary.
# When `as_dict` is false, then `data` should be a tuple or a list.

unpacked = unpack_ctrl.from_dict(data_type, data) # used when as_dict is true.
unpacked = unpack_ctrl.from_tuple(data_type, data) # used when as_dict is false.
```

## PackConfig configuration objects for pack_ctrl
`PackConfig` objects provide the following options:
```python
from tmsgpack import PackConfig

config = PackConfig(
    p_shortcuts=True, sort_keys=False, p_str_keys=False, use_single_float=False,
)
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
```
## UnpackConfig configuration objects for unpack_ctrl
`UnpackConfig` objects provide the following options:
```python
from tmsgpack import UnpackConfig

config = UnpackConfig(
    u_shortcuts=True, u_str_keys=False,
    read_size=16*1024, max_buffer_size=0,
    max_str_len=-1, max_bin_len=-1, max_list_len=-1, max_dict_len=-1,
)
"""
Config object for unpack_ctrl.options

    :param bool u_shortcuts:
        If true, unpack dicts, tuples, lists without calling from_dict/from_tuple.
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
```
## Packing and Unpacking dataclass objects
Here are the parts of one unit test that shows end-to-end packing and unpacking
of dataclass objects:

For the setup, we import tools and define the controllers:
```python
from tmsgpack import packb, unpackb, PackConfig, UnpackConfig
from dataclasses import dataclass, is_dataclass, fields
from typing import Dict

@dataclass
class TypedPackCtrl:
    def from_obj(self, obj):
        if type(obj) is tuple: return False, 'tuple', obj  # Special case for tuples.
        if not is_dataclass(obj): raise TypeError(f'Cannot serialize {type(obj)} object.')
        as_dict = not getattr(obj, 'as_list', False)
        object_type = obj.__class__.__name__
        if as_dict:
            data = {
                field.name: getattr(obj, field.name)
                for field in fields(obj)
            }
        else:
            data = [
                getattr(obj, field.name)
                for field in fields(obj)
            ]
        return as_dict, object_type, data
    options: PackConfig

    def pack(self, data):
        return packb(data, pack_ctrl=self)

@dataclass
class TypedUnpackCtrl:
    constructors: Dict[str, callable]
    def from_dict(self, ctype, data): return self.constructors[ctype](**data)
    def from_tuple(self, ctype, data): return self.constructors[ctype]( *data)
    options: UnpackConfig

    def unpack(self, packed):
        return unpackb(packed, unpack_ctrl=self)

def pc(**kwargs): return TypedPackCtrl(options=PackConfig(**kwargs))
def uc(fns, **kwargs):
    return TypedUnpackCtrl(
        constructors={fn.__name__:fn for fn in fns},
        options=UnpackConfig(**kwargs),
    )
```
Notes:
* For conveninence, we added methods `pack_ctrl.pack(data)` and
  `unpack_ctrl.unpack(packed)`.
* The method `pack_ctrl.from_obj` decides whether to represent the dataclass object
  as a key-value dict or as a more compact list of values.
* It extracts the properties of the `obj` and sets the values `as_dict`, `object_type`
  and `data` appropriately.
* In this implementation, object types are the unqualified class names. There is
  a possibility that one class from one package can have the same name as a different
  class from a different package.
* Fully resolving naming spaces is a deep design problem.  You need to decide what
  you mean by 'meaning'.  Here, we exploit this overloadability...
* The `unpack_ctrl` object is created with a list of available constructor functions.

Now, we can define the data classes to be packed and unpacked:
```python
@dataclass
class Foo:
    x: int = 1
    y: str = 'Y'

@dataclass
class Bar:
    x: int = 1
    y: str = 'Y'
    as_list = True
```
Notes:
* Class Bar has a class property `as_list=True`.  It will be packed compactly as
  a parameter value list.

Here is a simple test runner to be used for several tests:
```python
def run(input, expected=None):
    if expected is None: expected = input

    constructors = [Foo, Bar]

    pack_ctrl    = pc()
    unpack_ctrl  = uc(constructors)

    packed = pack_ctrl.pack(input)
    output = unpack_ctrl.unpack(packed)

    assert output == expected
```

The `Foo()` and `Bar()` objects are packed and unpacked correctly:
```python
def test_typed_foobar():
    run(Foo())   # Encoded as a typed dict
    run(Bar())   # Encoded as a typed list
    run((1,2,3)) # Tuples are encoded as a typed list with object_type=None.
    run([1,2,3]) # Tuples are encoded as a typed list with object_type=False.
    run({'hello':'world'}) # Dicts are encoded as a typed dict with object_type=None.
```

