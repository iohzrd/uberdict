from collections import Mapping
from functools import partial
import sys

import pytest

from uberdict import _descend, _get, udict

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    import mock
except ImportError:
    from unittest import mock


from collections import namedtuple

version_info = namedtuple('version_info',
                          'major,minor,micro,releaselevel,serial')

if sys.version_info[0] < 3:
    def b(s):
        return s.encode('utf8') if not isinstance(s, str) else s

    def u(s):
        return s.decode('utf8') if isinstance(s, str) else s
else:
    def b(s):
        return s.encode('utf8') if not isinstance(s, bytes) else s

    def u(s):
        return s.decode('utf8') if isinstance(s, bytes) else s


class DefaultDict(udict):

    def __init__(self, default_factory, *args, **kwargs):
        assert callable(default_factory)
        self.default_factory = default_factory
        udict.__init__(self, *args, **kwargs)

    def __missing__(self, key):
        return self.default_factory()


def fail_factory(*args, **kwargs):
    pytest.fail()


# test utility for getting at the "real" mappings of a dict
def items(d):
    """
    Get the items of `d` (a dict/udict) in sorted order as
    they would be returned if `d` were a plain dict.
    """
    try:
        elems = dict.iteritems(d)
    except AttributeError:
        elems = dict.items(d)
    return sorted(elems)


def mkdict(cls, *args, **kwargs):
    # defaultdict needs type as first arg; we use None for testing
    if cls is DefaultDict:
        cls = partial(cls, type(None))
    return cls(*args, **kwargs)


@pytest.fixture
def dict_():
    return {
        'a': {'b': 'a->b'},
        '1': {'2': {'3': '1->2->3'}},
        'a.b': 'a.b',
        'c': 'c',
    }


@pytest.fixture(params=[dict, udict, DefaultDict])
def alldictfactory(request):
    return request.param


@pytest.fixture(params=[udict, DefaultDict])
def customdictfactory(request):
    return request.param


@pytest.fixture
def udict_(dict_):
    return udict.fromdict(dict_)


@pytest.fixture
def defaultdict_(dict_):
    return DefaultDict(lambda: None, dict_)


def test_get_bad_type(customdictfactory):
    with pytest.raises(TypeError):
        _get(None, None)
    with pytest.raises(TypeError):
        _get({}, {})


def test_get_present(customdictfactory):
    dct = mkdict(customdictfactory, {'a': 1})
    assert _get(dct, 'a') == 1


def test_get_custom_getitem():

    class C(object):

        def __getitem__(self, key):
            if key == 'sentinel':
                return mock.sentinel
            raise KeyError(key)

    c = C()
    assert _get(c, 'sentinel') is mock.sentinel
    with pytest.raises(KeyError):
        _get(c, 'missing')


def test_descend_top_level(dict_, alldictfactory):
    dct = mkdict(alldictfactory, dict_)
    with pytest.raises(ValueError):
        _descend(dct, 'c')


def test_descend_one_dot_match_all(dict_, alldictfactory):
    dct = mkdict(alldictfactory, dict_)
    val, token = _descend(dct, 'a.b')
    assert val is dct['a']
    assert token == 'b'


def test_descend_one_dot_match_allbutlast(dict_, alldictfactory):
    # matches all but last token
    dct = mkdict(alldictfactory, dict_)
    val, token = _descend(dct, 'a.z')
    assert val is dct['a']
    assert token == 'z'


def test_descend_two_dot_match_all(dict_, alldictfactory):
    dct = mkdict(alldictfactory, dict_)
    val, token = _descend(dct, '1.2.3')
    assert val is dct['1']['2']
    assert token == '3'


def test_descend_two_dot_match_allbutlast(dict_, alldictfactory):
    dct = mkdict(alldictfactory, dict_)
    val, token = _descend(dct, '1.2.X')
    assert val is dct['1']['2']
    assert token == 'X'


def test_descend_two_dot_match_first(dict_, alldictfactory):
    dct = mkdict(alldictfactory, dict_)
    with pytest.raises(KeyError) as err:
        _descend(dct, '1.Z.X')
        assert err.value.args[0] == 'Z'


def test_init_noargs():
    assert items(udict()) == []


def test_init_kwargs():
    ud = udict(one=1, two=2)
    assert items(ud) == [('one', 1), ('two', 2)]


def test_init_iterable_arg():
    lst = [('one', 1), ('two', 2), ('three', 3)]
    ud = udict(iter(lst))
    assert items(ud) == sorted(lst)


def test_init_dict_arg():
    d = {
        'a': 1,
        'b': 2,
        'c': 3
    }
    ud = udict(d)
    assert items(ud) == items(d)


def test_init_type():
    assert isinstance(udict(), udict)
    assert isinstance(udict(), dict)


def test_udict_is_dict_subclass():
    assert issubclass(udict, dict)


def test_udict_is_mapping():
    assert isinstance(udict(), Mapping)


def test_udict_is_mapping_subclass():
    assert issubclass(udict, Mapping)


def test_init_dict_arg_nested_dicts():
    d = {'foo': {'foo': 'bar'}}
    ud = udict(d)
    assert type(ud['foo']) is dict
    assert items(d) == [('foo', udict(foo='bar'))]


def test_init_dict_arg_dotted_key():
    d = {'a.b': 'a.b', 'a': 'a'}
    ud = udict(d)
    assert items(ud) == items(d)


def test_init_dict_arg_dotted_key_and_nested():
    d = {
        'a.b': 'a.b',
        'c': 'cc',
        'a': {'b': 'a->b'}
    }
    ud = udict(d)
    elems = items(ud)
    assert elems == [
        ('a', {'b': 'a->b'}),
        ('a.b', 'a.b'),
        ('c', 'cc')
    ]
    assert type(elems[0][1]) is dict  # not a udict!


def test_init_udict_arg():
    orig = udict({
        'a': {'b': 'a->b'},
        'c': udict({'d': 'c->d'})
    })
    ud = udict(orig)
    elems = items(ud)
    assert elems == [
        ('a', {'b': 'a->b'}),
        ('c', udict(d='c->d'))
    ]
    assert type(elems[0][1]) is dict
    assert type(elems[1][1]) is udict


def test_equality_with_dict():
    assert {} == udict()
    assert udict() == {}
    d = {'foo': {'bar': 'barbar'}}
    ud = udict(foo=udict(bar='barbar'))
    assert d == ud
    assert ud == d
    assert {} != udict(x='x')
    assert {'x': 'x'} != udict()
    assert udict(a=None) != udict(a={})


def test_equality_with_dict_dotted_key():
    d = {'foo.bar': ''}
    ud = udict({'foo.bar': ''})
    assert d == ud
    assert ud == d


def test_equality():
    assert udict() == udict()
    assert udict() != udict(x='')
    assert udict(x='') != udict()

    assert udict(a=0) == udict(a=0)
    assert udict(a=0) == udict(a=0.0)
    assert udict(a=0) != udict(b=0)
    assert udict(a=0) != udict(a='0')
    assert udict(a=0) != udict(a=1)
    assert udict(a=None) != udict(a={})
    assert udict(a={}) == udict(a=udict())

    ud1, ud2 = udict(a=udict()), udict(a=udict(a=None))
    assert ud1 != ud2
    assert ud2 != ud1

    ud1, ud2 = udict({'a.b': ''}), udict(a=udict(b=''))
    assert ud1 != ud2
    assert ud2 != ud1


def test_getitem_nonstring_key():
    ud = udict()
    ud[1] = 'one'
    assert ud[1] == 'one'


def test_getitem_none_key():
    ud = udict()
    ud[None] = 'nope'
    assert ud[None] == 'nope'


# @pytest.mark.skipif('sys.version_info[0] > 2')
def test_getitem_bytes_key():
    ud = udict()
    ud[b('one')] = 1
    assert ud[b('one')] == 1


def test_getitem_unicode_key():
    ud = udict()
    ud[u('one')] = 1
    assert ud[u('one')] == 1


def test_getitem_top_level_returns_value():
    obj = object()
    ud = udict(one=obj)
    assert ud['one'] is obj


def test_getitem_top_level_fail_raises_keyerror():
    ud = udict(one=1)
    with pytest.raises(KeyError):
        ud['two']


def test_getitem_multilevel_returns_value():
    ud = udict.fromdict({
        'one': {
            'two': 'one->two'
        },
        'a': {
            'b': {'c': 'a->b->c'}
        }
    })
    assert ud['one.two'] == 'one->two'
    assert ud['a.b'] == {'c': 'a->b->c'}
    assert ud['a.b.c'] == 'a->b->c'


def test_getitem_multilevel_fail():
    ud = udict.fromdict({
        'one': {
            'two': 'one->two'
        },
        'a': {
            'b': {'c': 'a->b->c'}
        }
    })
    try:
        ud['one.three']
        pytest.fail()
    except KeyError as e:  # success
        # verify args contains first failing token
        assert e.args == ('three',)
    try:
        ud['a.b.x']
        pytest.fail()
    except KeyError as e:
        assert e.args == ('x',)

    with pytest.raises(TypeError):
        # ud['a.b.c'] doesn't support indexing
        ud['a.b.c.d']


def test_getitem_nested_through_non_dict_typeerror():
    """
    TypeError should be raised when trying to traverse through
    an object that doesn't support `__getitem__`.
    """
    ud = udict(one=udict(two=2))
    with pytest.raises(TypeError):
        ud['one.two.three']


class BadDict(object):

    def __init__(self, **kwargs):
        self.d = kwargs

    def __getitem__(self, key):
        return self.d[key]


def test_baddict():
    bd = BadDict(a=BadDict(b='a->b'))
    assert bd['a']['b'] == 'a->b'
    with pytest.raises(KeyError):
        bd['missing']


def test_getitem_nested_through_non_dict_keyerror():
    """
    KeyError should be raised when trying to traverse through
    an object that does support `__getitem__` if the object
    raises KeyError due to no such key.
    """
    ud = udict(
        a=BadDict()
    )
    with pytest.raises(KeyError):
        ud['a.b']


def test_getitem_nested_through_non_dict_success():
    ud = udict(a=BadDict(b=udict(c='a->b->c')))
    assert ud['a.b'] == udict(c='a->b->c')
    assert ud['a.b.c'] == 'a->b->c'


def test_getitem_dotted_key_top_level_miss():
    ud = udict({'a.b': 2})
    with pytest.raises(KeyError):
        ud['a.b']


def test_getitem_subclass_missing():
    ud = DefaultDict(int)
    assert ud['missing'] == 0
    ud = DefaultDict(lambda: None)  # not type(None) for py2 compability
    assert ud['missing'] is None


def test_setitem_int_key():
    ud = udict()
    ud[1] = 'one'
    assert items(ud) == [(1, 'one')]


def test_setitem_none_key():
    ud = udict()
    ud[None] = 'None'
    assert items(ud) == [(None, 'None')]


def test_setitem_top_level():
    ud = udict()
    ud['one'] = 1
    assert items(ud) == [('one', 1)]


def test_setitem_second_level_first_exists():
    ud = udict()
    ud['one'] = udict()
    ud['one.two'] = 2
    assert items(ud) == [('one', udict(two=2))]


def test_setitem_second_level_first_missing():
    ud = udict()
    try:
        ud['one.two'] = 2
        pytest.fail()
    except KeyError as e:
        assert e.args == ('one',)


def test_delitem_top_level_exists():
    ud = udict({'one': 1})
    del ud['one']
    assert items(ud) == []


def test_delitem_top_level_missing():
    ud = udict(one=1)
    try:
        del ud['two']
        pytest.fails()
    except KeyError as e:
        assert e.args == ('two',)


def test_delitem_second_level_first_missing():
    ud = udict(one=1)
    try:
        del ud['two.three']
        pytest.fails()
    except KeyError as e:
        assert e.args == ('two',)


def test_delitem_second_level_first_exists_fail():
    ud = udict.fromdict({
        'one': {
            'two': 'one->two'
        }
    })
    try:
        del ud['one.three']
        pytest.fails()
    except KeyError as e:
        assert e.args == ('three',)


def test_delitem_second_level_success():
    ud = udict.fromdict({
        'one': {
            'two': 2,
            'blah': {
                'three': 3
            }
        }
    })
    del ud['one.blah']
    assert items(ud) == [
        ('one', udict(two=2))
    ]
    del ud['one.two']
    assert items(ud) == [('one', udict())]


def test_delitem_dotted_key():
    d = {'a.b': ''}
    ud = udict(d)
    with pytest.raises(KeyError):
        del ud['a']
    with pytest.raises(KeyError):
        del ud['a.b']


def test_pop_present():
    ud = udict(a='a', b='b')
    val = ud.pop('b')
    assert val == 'b'
    ud == udict(a='a')


def test_pop_missing_toplevel_no_default():
    with pytest.raises(KeyError):
        udict().pop('missing')
    with pytest.raises(KeyError):
        udict(a='aa').pop('aa')


def test_pop_missing_second_level_no_default():
    with pytest.raises(KeyError):
        udict().pop('a.b')


def test_pop_missing_default():
    udict().pop('foo', 'bar') == 'bar'


def test_pop_missing_second_level_default():
    assert udict().pop('a.b', mock.sentinel) is mock.sentinel
    assert udict(a={}).pop('a.b', mock.sentinel) is mock.sentinel


def test_pop_nested():
    d = {
        'a': 'aa',
        'b': 'bb',
        'a': {'b': {'c': 'a->b->c'}},
    }
    ud = udict.fromdict(d)
    assert ud['a.b.c'] == 'a->b->c'
    val = ud.pop('a.b.c')
    assert val == 'a->b->c'


def test_pop_dotted():
    d = {
        'a': udict(b='a->b'),
        'b': 'bb',
        'a.b': 'a.b'
    }
    ud = udict.fromdict(d)
    val = ud.pop('a.b')
    assert val == 'a->b'
    assert ud['a'] == udict()


def test_popitem_empty():
    with pytest.raises(KeyError):
        udict().popitem()


def test_popitem_nonempty():
    ud = udict(a='aa')
    assert ud
    assert ud.popitem() == ('a', 'aa')
    assert not ud


def test_popitem_dotted():
    orig = udict.fromdict({
        'a': {'b': 'a->b'},
        'a.b': 'a.b'
    })
    # popitem removes a random (key, value) pair, so do that enough
    # times to verify that when doing popitem on above, we only
    # ever see the 'a.b' top-level mapping removed or the
    # 'a' top-level mapping removed, never the child ('b', 'a->b') mapping
    for i in range(20):
        ud = udict.fromdict(orig)
        assert ud.popitem() in (
            ('a', udict(b='a->b')),
            ('a.b', 'a.b')
        )


def test_hasattr_top_level_success():
    assert hasattr(udict(one=1), 'one')


def test_hasattr_top_level_fail():
    assert not hasattr(udict(one=1), 'two')


def test_hasattr_nested():
    ud = udict.fromdict({
        'a': {
            'b': 'a->b'
        }
    })
    assert not hasattr(ud, 'a.b')
    assert hasattr(ud, 'a')
    assert hasattr(ud['a'], 'b')


def test_hasattr_dotted():
    ud = udict({'a.b': 'a.b'})
    assert hasattr(ud, 'a.b')
    assert not hasattr(ud, 'a')


def test_hasattr_nested_dotted():
    ud = udict.fromdict({
        'a': {
            'b': 'a->b',
            'c': 'a->c'
        },
        'a.b': 'a.b'
    })
    assert hasattr(ud, 'a')
    assert hasattr(ud, 'a.b')
    assert not hasattr(ud, 'a.c')


def test_getattr_top_level_success():
    ud = udict(one=1)
    assert ud.one == 1


def test_getattr_top_level_fail():
    ud = udict(one=1)
    try:
        ud.two
        pytest.fail()
    except AttributeError as e:
        assert e.args == ("no attribute 'two'",)


def test_getattr_dotted_key():
    ud = udict.fromdict({
        'a.b': 'abab',
        'a': {'b': 'abab'}
    })
    uda = ud['a']
    assert uda == udict(b='abab')
    assert getattr(ud, 'a.b') == 'abab'
    assert getattr(ud, 'a') == uda
    assert ud.a == uda
    assert ud.a.b == 'abab'


def test_setattr_objectstyle():
    ud = udict()
    ud.one = 1
    assert len(ud) == 1
    ud.one = udict()
    ud.one.two = 2
    assert ud.one.two == 2
    assert ud['one']['two'] == 2


def test_setattr_dotted_key():
    ud = udict(one=udict(two=2))
    setattr(ud, 'one.two', 'onetwo')
    assert ud['one.two'] == 2
    assert getattr(ud, 'one.two') == 'onetwo'
    assert ud['one'] == udict(two=2)
    assert getattr(ud, 'one') == udict(two=2)


def test_delattr_success():
    ud = udict(one=1)
    del ud.one
    assert len(ud) == 0


def test_delattr_fail():
    ud = udict(one=1)
    try:
        del ud.two
        pytest.fail()
    except AttributeError as e:
        assert e.args == ("no attribute 'two'",)


def test_delattr_dotted_key_present():
    d = {
        'one': {'two': 'one->two'}
    }
    ud = udict(d)
    del ud['one.two']
    assert items(ud) == [('one', {})]


def test_delattr_dotted_key_missing():
    d = {
        'one.two': 'one.two'
    }
    ud = udict(d)
    with pytest.raises(KeyError):
        del ud['one.two']
    assert ud == d


def test_delattr_dotted_key_present_dotted_toplevel():
    d = {
        'one.two': 'one.two',
        'one': {
            'two': 'one->two'
        }
    }
    ud = udict.fromdict(d)
    del ud['one.two']
    assert items(ud) == [
        ('one', udict()),
        ('one.two', 'one.two')
    ]


def test_get_missing_nodefault():
    assert udict().get('x') is None


def test_get_missing_default():
    assert udict().get('x', 1) == 1


def test_get_missing_child_nodefault():
    assert udict(one=udict()).get('one.two') is None


def test_get_missing_child_default():
    assert udict(one=udict()).get('one.two', 3) == 3


def test_get_nested_child():
    ud = udict(one=udict(two=2))
    assert ud.get('one.two') == 2


def test_get_none_nodefault():
    assert udict().get(None) is None


def test_get_none_default():
    assert udict().get(None, 3) == 3


def test_fromdict_classmethod():
    ud = udict.fromdict({})
    assert isinstance(ud, udict)
    assert ud == udict()


def test_fromdict_nested_dicts():
    d = {
        'a': {
            'b': {
                'c': 'a->b->c'
            }
        }
    }
    ud = udict.fromdict(d)
    elems = items(ud)
    assert elems == [
        ('a', udict({'b': udict({'c': 'a->b->c'})}))
    ]
    assert type(elems[0][1]) is udict


def test_fromdict_dotted_key():
    d = {
        'a.b': 'a.b',
        'a': {
            'b': 'a->b'
        }
    }
    ud = udict.fromdict(d)
    elems = items(ud)
    assert elems == [
        ('a', udict(b='a->b')),
        ('a.b', 'a.b')
    ]
    assert type(elems[0][1]) is udict


def test_fromdict_udicts():
    d = {
        'one.two': 'one.two',
        'one': {
            'two': 'one->two'
        }
    }
    orig = udict.fromdict(d)
    ud = udict.fromdict(orig)
    assert items(ud) == items(d)


def test_fromkeys_classmethod():
    ud = udict.fromkeys([])
    assert ud == udict()


def test_fromkeys_no_value():
    assert udict.fromkeys([]) == udict()
    assert udict.fromkeys(range(5)) == udict((i, None) for i in range(5))


def test_fromkeys_value():
    ud = udict.fromkeys([], 1)
    assert ud == udict()
    assert ud == dict.fromkeys([], 1)

    ud = udict.fromkeys(range(1), 1)
    assert ud == udict.fromdict({0: 1})
    assert ud == dict.fromkeys(range(1), 1)

    ud = udict.fromkeys(range(10), 0)
    assert ud == udict((i, 0) for i in range(10))
    assert ud == dict.fromkeys(range(10), 0)


def test_fromkeys_dotted_keys():
    elems = ['a.b', 'a', 'b']
    ud = udict.fromkeys(elems, udict())
    assert items(ud) == [
        ('a', udict()),
        ('a.b', udict()),
        ('b', udict())
    ]


def test_todict():
    ud = udict(foo='foofoo')
    d = ud.todict()
    assert d == {'foo': 'foofoo'}
    assert isinstance(d, dict)
    assert not isinstance(d, udict)


def test_todict_nested():
    ud = udict(foo=udict(bar='barbar'))
    d = ud.todict()
    assert isinstance(d['foo'], dict)
    assert not isinstance(d['foo'], udict)
    assert items(d) == [
        ('foo', {'bar': 'barbar'})
    ]


def test_todict_dotted_keys():
    orig = {
        'one.two': 'one.two',
        'one': {'two': 'one->two'}
    }
    ud = udict.fromdict(orig)
    assert isinstance(ud['one'], udict)
    d = ud.todict()
    assert items(d) == [
        ('one', {'two': 'one->two'}),
        ('one.two', 'one.two')
    ]
    assert type(items(d)[0][1]) is dict


def test_keys():
    d = dict(foo=dict(bar='barbar'))
    ud = udict.fromdict(d)
    assert ud.keys()
    assert ud.keys() == d.keys()


def test_keys_dotted():
    d = {
        'a.b': 'a.b',
        'a': {'b': 'a->b'}
    }
    ud = udict(d)
    assert sorted(ud.keys()) == sorted(d.keys())


def test_pickle_dumpsloads_simple():
    orig = udict({'one': 1, 'two': 2})
    unpickled = pickle.loads(pickle.dumps(orig))
    assert items(unpickled) == items(orig)
    assert isinstance(unpickled, udict)


def test_pickle_dumpsloads_dotted():
    orig = udict({'one.two': 'one.two'})
    pickled = pickle.dumps(orig)
    unpickled = pickle.loads(pickled)
    assert items(unpickled) == items(orig)


def test_pickle_dumpsloads_nested():
    orig = udict({'one': {'two': 'one->two'}})
    unpickled = pickle.loads(pickle.dumps(orig))
    assert items(unpickled) == items(orig)


def test_pickle_dumpsloads_nested_dotted():
    orig = udict.fromdict({
        'one': {
            'two': 'one->two'
        },
        'one.two': 'one.two'
    })
    unpickled = pickle.loads(pickle.dumps(orig))
    # assert unpickled == orig
    assert items(unpickled) == items(orig)
    assert isinstance(unpickled, udict)
    assert isinstance(unpickled['one'], udict)


def test_copy():
    orig = udict(
        foo=udict(
            bar={'baz': 'bazbaz'},
            boo=udict(boz='bozboz')
        )
    )
    assert isinstance(orig, udict)
    assert isinstance(orig['foo'], udict)
    assert isinstance(orig['foo']['bar'], dict)
    assert isinstance(orig['foo']['boo'], udict)
    copy = orig.copy()
    assert isinstance(copy, udict)
    assert orig == copy
    assert copy == orig
    assert copy.foo is orig.foo
    assert copy.foo.bar is orig.foo.bar
    assert copy.foo.boo is orig.foo.boo


def test_setdefault_value_plain_not_present():
    ud = udict()
    child = udict()
    res = ud.setdefault('child', child)
    assert ud['child'] is res
    assert ud['child'] is child
    assert set(ud.keys()) == set(['child'])


def test_setdefault_value_plain_present():
    child = udict()
    ud = udict(child=child)
    res = ud.setdefault('child', udict())
    assert ud['child'] is child
    assert ud['child'] is res


def test_setdefault_value_dotted_key_not_present():
    ud = udict(a=udict())
    child = udict()
    res = ud.setdefault('a.b', child)
    assert res is child
    assert ud['a.b'] is child


def test_setdefault_value_dotted_key_present():
    ud = udict.fromdict({
        'a': {
            'b': {
                'c1': 'abc'
            }
        }
    })
    res = ud.setdefault('a.b', udict())
    res['c2'] = 'cba'
    assert set(ud.keys()) == set(['a'])
    assert ud.get('a.b.c2') == 'cba'
    assert ud.get('a.b.c1') == 'abc'


def test_contains_plain_not_present():
    ud = udict(foo='bar')
    assert None not in ud
    assert 'foo' in ud
    assert 'bar' not in ud
    ud.pop('foo')
    assert ud == udict()
    assert 'foo' not in ud


def test_contains_plain_present():
    assert 'foo' in udict(foo='bar')
    assert 'bar' not in udict(foo='bar')
    assert None in udict.fromdict({None: ''})
    ud = udict.fromdict({1: 2, 3: 4})
    assert 1 in ud
    assert 2 not in ud
    assert 3 in ud


def test_contains_dotted_not_present():
    assert 'a.b' not in udict()
    assert 'foo.bar' not in udict(foo=udict(notbar='notbar'))


def test_contains_dotted_present_nonleaf():
    assert 'a.b' in udict(a=udict(b=udict(c=udict())))


def test_contains_dotted_present_leaf():
    assert 'a.b.c' in udict(a=udict(b=udict(c=udict())))


def test_contains_dotted_partial():
    assert 'a.b.c' not in udict(a=udict())


def test_len():
    assert len(udict()) == 0
    assert len(udict(a='')) == 1
    assert len(udict(a=udict(a=''))) == 1


def test_clear():
    ud = udict(a='')
    ud.clear()
    assert ud == udict()

    ud = udict({'a.b': ''})
    ud.clear()
    assert ud == udict()


def test_values():
    assert list(udict().values()) == []
    ud = udict(a='aa')
    assert list(ud.values()) == ['aa']
    ud['b'] = 'bb'
    assert sorted(ud.values()) == ['aa', 'bb']
    ud['a'] = udict(b='ab')


def test_values_dotted_keys():
    ud = udict.fromdict({
        'a': dict(b='ab'),
        'b': 'bb',
        'a.b': 'a.ba.b'
    })
    values = ud.values()
    assert 'bb' in values
    assert 'a.ba.b' in values
    assert udict(b='ab') in values
    del ud['a']
    assert sorted(ud.values()) == ['a.ba.b', 'bb']


@pytest.mark.skipif(sys.version_info >= (3,),
                    reason="only tested on python2")
def test_has_key():
    ud = udict()
    assert not ud.has_key('a')  # noqa
    ud['a'] = None
    assert ud.has_key('a')  # noqa
    assert not ud.has_key(None)  # noqa


def test_update():
    orig = {
        'a': {'b': 'a->b'},
        'a.b': 'a.b',
        'c': 'c'
    }
    ud = udict.fromdict(orig)
    ud.update({'a': 'a'})
    assert ud['a'] == 'a'
    assert ud['c'] == orig['c']
    with pytest.raises(TypeError):
        ud['a.b']  # ud['a'] doesn't support __getitem__
    assert getattr(ud, 'a.b') == 'a.b'

    ud = udict.fromdict(orig)
    ud.update(udict({'a.b': 'b.a'}))
    assert ud['a.b'] == 'a->b'
    assert ud['a'] == udict(b='a->b')
    assert ud['c'] == 'c'


def test_dir_includes_dict_methods():
    attrs = set(dir(udict()))
    for attr in dir({}):
        assert attr in attrs


def test_dir_includes_udict_instance_methods():
    assert 'todict' in dir(udict())


def test_dir_includes_class_methods():
    assert 'fromdict' in dir(udict())


def test_dir_includes_keys():
    ud = udict(foo='foofoo', bar='barbar')
    attrs = dir(ud)
    assert 'foo' in attrs
    assert 'bar' in attrs


def test_dir_includes_dotted_keys():
    ud = udict({'a.b.c': 'a.b.c'})
    assert 'a.b.c' in dir(ud)


def test_dir_omits_nested_keys():
    ud = udict.fromdict({
        'a': {
            'b': 'a->b'
        },
        'a.c': 'a.c'
    })
    attrs = dir(ud)
    assert 'a' in attrs
    assert 'a.b' not in attrs
    assert 'a.c' in attrs


def test_subclass_missing_getitem_success():
    ud = DefaultDict(fail_factory, a=3)
    assert ud['a'] == 3


def test_subclass_missing_getitem_fail():
    ud = DefaultDict(int)
    assert ud['b'] == int()


def test_subclass_missing_contains():
    ud = DefaultDict(int, b=1)
    assert 'a' not in ud
    assert 'b' in ud


def test_subclass_missing_get_fail():
    ud = DefaultDict(int)
    assert ud.get('b') is None
    assert ud.get('b', 'foo') == 'foo'


def test_subclass_missing_delitem_success():
    ud = DefaultDict(int, a=1)
    del ud['a']
    assert 'a' not in ud


def test_subclass_missing_delitem_fail():
    ud = DefaultDict(fail_factory)
    with pytest.raises(KeyError):
        del ud['a']


def test_subclass_missing_setdefault_notpresent():
    ud = DefaultDict(fail_factory)
    obj = object()
    res = ud.setdefault('a', obj)
    assert res is obj
    assert ud['a'] is res


def test_subclass_missing_setdefault_present():
    ud = DefaultDict(fail_factory)
    obj = object()
    ud['a'] = obj
    res = ud.setdefault('a', object())
    assert res is obj


def test_subclass_missing_todict():
    # verifying that it doesn't use __missing__ inadvertently
    ud = DefaultDict(fail_factory)
    ud['a'] = 1
    assert ud.copy() == ud


def test_subclass_missing_getattr():
    ud = DefaultDict(fail_factory)
    ud.foo = 'bar'
    assert getattr(ud, 'foo') == 'bar'
    with pytest.raises(AttributeError):
        ud.moo


def test_subclass_missing_instance_variable_ignored():
    class MyDict(udict):
        def __init__(self, *args, **kwargs):
            udict.__init__(self, *args, **kwargs)
            self.__dict__['__missing__'] = fail_factory
    md = MyDict()
    assert md.__missing__ is fail_factory
    with pytest.raises(KeyError):
        md['a']
    with pytest.raises(AttributeError):
        md.a


@pytest.mark.parametrize('version_info', [
    version_info(2, 7, 13, 'final', 0),
    version_info(3, 6, 2, 'final', 0),
])
def test_iteritems(version_info):
    assert version_info.major in (2, 3)
    sys.modules.pop('uberdict', None)
    dct = mock.MagicMock()
    method = 'iteritems' if version_info[0] == 2 else 'items'
    with mock.patch.object(sys, 'version_info') as v_info:
        for k in version_info._asdict():
            setattr(v_info, k, getattr(version_info, k))
        import uberdict
        uberdict.iteritems(dct)
        getattr(dct, method).assert_called_once_with()
