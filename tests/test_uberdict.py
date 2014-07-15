from uberdict import UberDict as udict

try:
    import cPickle as pickle
except ImportError:
    import pickle

import pytest


def test_empty():
    assert len(udict()) == 0


def test_init_kwargs():
    assert len(udict(one=1, two=2)) == 2


def test_init_list_arg():
    assert len(udict([('one', 1), ('two', 2), ('three', 3)])) == 3


def test_init_dict_arg():
    assert udict(foo='bar') == udict({'foo': 'bar'})


def test_init_dict_arg_nested_dicts():
    d = {'foo': {'foo': 'bar'}}
    ud = udict(d)
    assert type(ud['foo']) is dict


def test_dict_equality():
    assert {} == udict()
    assert udict() == {}
    d = dict(foo=dict(bar='barbar'))
    ud = udict(foo=udict(bar='barbar'))
    assert d == ud
    assert ud == d


def test_getitem_int_key():
    b = udict()
    b[1] = 'one'
    assert b[1] == 'one'


def test_getitem_none_key():
    b = udict()
    b[None] = 'nope'
    assert b[None] == 'nope'


def test_getitem_top_level_success():
    b = udict(one=1)
    assert b['one'] == 1
    assert b.__getitem__('one') == 1


def test_getitem_top_level_fail():
    b = udict(one=1)
    with pytest.raises(KeyError):
        b['two']


def test_getitem_second_level_success():
    b = udict(one=udict(two=2))
    assert b['one.two'] == 2
    assert b.__getitem__('one.two') == 2


def test_getitem_second_level_fail():
    b = udict(one=udict(two=2))
    try:
        b['one.three']
        pytest.fail()
    except KeyError as e:  # success
        # verify args contains first failing token
        assert e.args == ('three',)


def test_getitem_nested_through_non_udict():
    b = udict(one=udict(two=2))
    try:
        b['one.two.three']
        pytest.fail()
    except KeyError as e:
        assert e.args == ('three',)


def test_setitem_int_key():
    b = udict()
    b[1] = 'one'
    assert len(b) == 1


def test_setitem_none_key():
    b = udict()
    b[None] = 'nope'
    assert len(b) == 1


def test_setitem_top_level():
    b = udict()
    b['one'] = 1
    assert len(b) == 1


def test_setitem_second_level_existing_first():
    b = udict()
    b['one'] = udict()
    b['one.two'] = 2
    assert len(b) == 1
    assert b['one'] == udict(two=2)


def test_setitem_second_level_nonexisting_first():
    b = udict()
    try:
        b['one.two'] = 2
        pytest.fail()
    except KeyError as e:
        assert e.args == ('one',)


def test_delitem_top_level_existing():
    b = udict(one=1)
    del b['one']
    assert len(b) == 0
    assert 'one' not in b


def test_delitem_top_level_nonexisting():
    b = udict(one=1)
    try:
        del b['two']
        pytest.fails()
    except KeyError as e:
        assert e.args == ('two',)


def test_delitem_second_level_non_existing_first():
    b = udict(one=1)
    try:
        del b['two.three']
        pytest.fails()
    except KeyError as e:
        assert e.args == ('two',)


def test_delitem_second_level_fail_existing_first():
    b = udict(one=udict(two=2))
    try:
        del b['one.three']
        pytest.fails()
    except KeyError as e:
        assert e.args == ('three',)


def test_delitem_second_level_success():
    b = udict(one=udict(two=2, blah=udict(three=3)))
    del b['one.blah']
    assert 'one' in b
    assert 'two' in b['one']
    assert b == udict(one=udict(two=2))
    del b['one.two']
    assert b == udict(one=udict())


def test_getattr_top_level_success():
    b = udict(one=1)
    assert b.one == 1


def test_getattr_top_level_fail():
    b = udict(one=1)
    try:
        b.two
        pytest.fail()
    except AttributeError as e:
        assert e.args == ("no attribute 'two'",)


def test_setattr():
    b = udict()
    b.one = 1
    assert len(b) == 1
    b.one = udict()
    b.one.two = 2
    assert b.one.two == 2
    assert b['one']['two'] == 2


def test_delattr_success():
    b = udict(one=1)
    del b.one
    assert len(b) == 0


def test_delattr_fail():
    b = udict(one=1)
    try:
        del b.two
        pytest.fail()
    except AttributeError as e:
        assert e.args == ("no attribute 'two'",)


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
    d = dict(foo=dict(foo='foofoo'))
    ud = udict.fromdict(d)
    assert type(ud['foo']) is udict
    assert ud == udict(foo=udict(foo='foofoo'))
    d['foo']['bar'] = dict(baz='bazbaz')
    ud = udict.fromdict(d)
    assert type(ud['foo']['bar']) is udict
    assert d['foo']['bar']['baz'] == 'bazbaz'


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


def test_keys():
    # udict doesn't do anything with keys, but this verifies that
    # we don't have any problem using a built-in dict method
    d = dict(foo=dict(bar='barbar'))
    ud = udict.fromdict(d)
    assert ud.keys()
    assert ud.keys() == d.keys()


def test_pickle():
    orig = udict(
        foo=udict(
            bar='barbar',
            blah={'blah': 'blahblah'}
        )
    )
    unpickled = pickle.loads(pickle.dumps(orig))
    assert unpickled == orig
    assert isinstance(unpickled, udict)
    assert isinstance(unpickled['foo'], udict)
    assert isinstance(unpickled['foo']['blah'], dict)


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
