uberdict
========

A Python dict that supports attribute-style access as well as hierarchical keys.


Examples
========

```python
from uberdict import UberDict as udict

d = udict(name='UberDict')

# prints same as dict (pprint module still works with udict)
assert str(d) == "{'name': 'UberDict'}"

# accessible as normal dict or using attributes
assert d.name == d['name']

d.child = udict(name='subdict')
# nestable udicts easily accessible in either form
assert d.child.name == d['child.name']

# easy conversion back to dict with all nested udict converted to dict
d = udict(child=udict(name='child'))
plain = d.todict()
assert isinstance(plain['child'], dict)
assert not isinstance(plain['child'], udict)

# easy creation of udict with all dicts converted (recursively)
d = udict.fromdict({
    'child': {
        'child': {
            'name': 'subsubchild'
        }
    }
})
assert d.child.child.name == 'subsubchild'

# makes working with json in python more convenient:
import json
my_json = '''{
    "name": "UberDict",
    "child": { "name": "subdict" }
}'''
dj = udict.fromdict(json.loads(my_json))
assert dj.name == 'UberDict'
assert dj.child.name == 'subdict'

# equality with dicts is automatic
assert {'a': 'b'} == udict(a='b')
assert udict(a='b') == {'a': 'b'}

# hasattr/getattr/setattr/delattr work as expected
d = udict()
assert not hasattr(d, 'foo')
d.foo = 'foo'
d['bar'] = 'bar'
assert hasattr(d, 'foo')
assert hasattr(d, 'bar')
setattr(d, 'baz', 'bazbaz')
assert 'baz' in d
assert d['baz'] == 'bazbaz'
delattr(d, 'baz')
assert 'baz' not in d
del d['foo']  # works too
assert 'foo' not in d
assert not hasattr(d, 'foo')
```
