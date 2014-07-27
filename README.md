# uberdict

`uberdict.udict` is a Python `dict` class that supports attribute-style access
(`my_udict.result.status.code`) as well as hierarchical keys
(`my_udict.get('d.result.status.code')`).

Tested under py26, py27, py32, py33, py34, and pypy.

[![Build Status](https://travis-ci.org/eukaryote/uberdict.svg?branch=master)](https://travis-ci.org/eukaryote/uberdict)

# Key Features

## Easy Conversion from/to plain dict

The `__init__` method signature matches that of the stdlib's `dict`, so it can
be used as a drop-in replacement for `dict`. If you want to create a `udict`
from a plain `dict` as a deep copy that converts every plain `dict` value at
any level to an equivalent `udict`, use the `udict.fromdict` class method
(and for the reverse direction, use the `todict` instance method of a `udict`
instance):

```python
d = {
    'result': {
        'status': {
            'code': 200,
            'reason': 'OK'
        }
    }
}

# shallow udict copy, like plain `dict` (the `result` value is the original `dict`)
ud = udict(d)

# deep udict copy that recursively converts `dict` to `udict`:
ud = udict.fromdict(d)

# convert back to plain `dict` (recursively)
d = ud.todict()
```

## Attribute-Style Access

The values in a `udict` may be accessed as if they were attributes on the `udict`,
like normal Python objects:

```python
d = {
    'result': {
        'status': {
            'code': 200,
            'reason': 'OK'
        }
    }
}
ud = udict.fromdict(d)

assert ud.result.status.code == ud['result']['status']['code']

# setting an attribute on the `udict` instance works like a normal dict insertion
ud.message = udict(lang='en', body='Hello, World!')

assert 'message' in ud
assert ud['message'] == ud.message
```


The standard Python attr methods (`hasattr`, `getattr`, `setattr`, and
`delattr`) work as expected.

```python
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

> Important: `getattr` and related functions don't interpret a `.` in keys
> in any special way, so you can always insert a key containing a `.` using
> `setattr`, and can retrieve the value for a key containing a `.` by using
> `getattr`.


```python
d = {
    'a': {
        'b': 'a->b'
    },
    'a.b': 'a.b'
}
ud = udict.fromdict(d)
setattr(ud, 'a.b', None)  # doesn't touch 'a'
assert ud['a.b'] is None
assert ud.a == d['a']
assert ud.a.b == 'a->b'```

## Dict-Style Access and Hierarchical Keys

Because a `udict` is a `dict`, you can of course access it like a `dict`:

```python
ud = udict({'foo': 1})
assert 'foo' in ud
ud['foo'] = 2
ud['foo'] += 1
assert ud.get('bar', 42) == 42
del ud['foo']
```

When a `udict` instance contains nested `udict` instances, you can do the
normal `dict` operations with dotted keys that traverse multiple levels
of the hierarchical structure:

```python
ud = udict.fromdict({
    'result': {
        'status': {
            'code': 200,
            'reason': 'OK'
        }
    }
})

assert ud['result.status.reason'] == 'OK'

# ud['result.status.reason'] would raise a `KeyError` if the `result` had
# no `status` or the `status` weren't a `dict`.
# use `get` if you're unsure of existence:
assert ud.get('result.foo.bar') is None
assert ud.get('result.foo.bar', 42) == 42

# dotted keys work as expected for other dict-style operations too:
ud['result.status.code'] = 400
assert 'result.status' in ud and 'result.status.reason' in ud
del ud['result.status.code']
```

## dict-compatible

Since a `udict` is a `dict`, it behaves like a `dict` even when used with
brittle code that requires a `dict` instance rather than something that
"quacks" like a `dict`. For example, the stdlib's pretty printing module,
`pprint`, generates a pretty, indented representation of a `udict` that is
identical to the one it generates for a plain `dict`, but `pprint` doesn't
use the dict-style representation for non-dicts even if they support all
the `dict` methods and register themselves as a `collections.Mapping`.

The `__init__` method signature matches that of the stdlib's `dict`, so it can
be used as a drop-in replacement for `dict` with no code-changes needed apart
from using `udict` instead of `dict` (assuming a suitable `import`).

The `str` and `repr` are identical as for a plain `dict` also, and a `udict`
is `==` to an "equivalent" `dict`


# Notes


## Avoiding Ambiguity of Dotted Keys

Consider the following `udict`:

```python
ud = udict.fromdict({
    'a': {
        'b': 'a->b'
    },
    'a.b': 'a.b'
})
```

When doing `ud['a.b']`, you might reasonably expect that to evaluate to
`'a.b'`, because there is a top-level `'a.b'` key. But it would
also be reasonable to expect `ud['a.b']` to evaluate to `'a->b'`, since
a dotted key is interpreted as a key that traverses a path from the base `udict`
through a sequence of one more child `dict` values, as described above.

In order to avoid such ambiguities, dict-style access like `ud['a.b']` or
`ud.get('a.b')` is *always* interpreted as if it were `ud['a']['b']` or
`ud.get('a', {}).get('b')`, respectively. That means you could never access the
top-level `'a.b'` in the `udict` above using dict-style access. You'll either
get the value of a nested `udict` or get a `KeyError` (or default value in
case of `udict.get`). To access the top-level `'a.b'` mapping,
use `getattr(ud, 'a.b')` instead.  The attribute-style accessors (`hasattr`,
`getattr`, `setattr`, and `delattr`) *always* interpret a key literally, with
no special treatment of keys that contain dots.

Thus, the simple rule to remember is:

> dict-style access with a dotted key is *always* interpreted hierarchically,
> and attribute-style access is *always* interpreted non-hierarchically.


## Reasoning about udict Operations

The following table shows how accessing a value on a `udict` "desugars" to
an equivalent sequence of operations on a plain `dict`:


| Udict Operation        | Equivalent Dict Operation(s) |
| ---------------------- | ---------------------------- |
| ud['a']                | d['a']                       |
| ud.get('a')            | d.get('a')                   |
| ud.get('a', 42)        | d.get('a', 42)               |
| ud.a                   | d['a']                       |
| getattr(d, 'a')        | d['a']                       |
| getattr(d, 'a', 42)    | d.get('a', 42)               |
| ud['a.b']              | d['a']['b']                  |
| ud.get('a.b')          | d.get('a', {}).get('b')      |
| ud.get('a.b', 42)      | d.get('a', {}).get('b', 42)  |
| getattr(d, 'a.b')      | d['a.b']                     |
| getattr(d, 'a.b', 42)  | d.get('a.b', 42)             |
| ud.a.b                 | d['a']['b']                  |


The only significant difference between operations on the left-side and those
on the right-side above is when an exception is raised due to there being no
suitable mapping (and no default as there might be with `get` and `getattr`).
In such cases, attribute-style access yields an `AttributeError` (matching
standard Python behavior for attribute access), whereas the equivalent
operation on a `dict` would yield a `KeyError`.
