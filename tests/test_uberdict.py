import sys

try:
    import cPickle as pickle
except ImportError:
    import pickle

import pytest


from uberdict import UberDict as udict


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


def test_init_dict_dotted_key():
    d = {'a.b': 'abab', 'c': 'cc', 'a': {'b': 'abab'}}
    ud = udict(d)
    assert d == ud
    assert ud == d
    assert 'a.b' in ud
    assert 'a' in ud


def test_dict_equality():
    assert {} == udict()
    assert udict() == {}
    d = dict(foo=dict(bar='barbar'))
    ud = udict(foo=udict(bar='barbar'))
    assert d == ud
    assert ud == d
    assert {} != udict(x='x')
    assert {'x': 'x'} != udict()
    assert {'foo.bar': ''} != udict('')


def test_dict_equality_dotted_key():
    d = {'foo.bar': ''}
    # the only way to get a dotted key into a udict is
    # by creating the udict from a dict containing such a key
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

    ud1, ud2 = udict(a=udict()), udict(a=udict(a=None))
    assert ud1 != ud2
    assert ud2 != ud1

    ud1, ud2 = udict({'a.b': ''}), udict(a=udict(b=''))
    assert ud1 != ud2
    assert ud2 != ud1


def test_getitem_int_key():
    ud = udict()
    ud[1] = 'one'
    assert ud[1] == 'one'


def test_getitem_none_key():
    ud = udict()
    ud[None] = 'nope'
    assert ud[None] == 'nope'


def test_getitem_top_level_success():
    ud = udict(one=1)
    assert ud['one'] == 1
    assert ud.__getitem__('one') == 1


def test_getitem_top_level_fail():
    ud = udict(one=1)
    with pytest.raises(KeyError):
        ud['two']


def test_getitem_second_level_success():
    ud = udict(one=udict(two=2))
    assert ud['one.two'] == 2
    assert ud.__getitem__('one.two') == 2


def test_getitem_second_level_fail():
    ud = udict(one=udict(two=2))
    try:
        ud['one.three']
        pytest.fail()
    except KeyError as e:  # success
        # verify args contains first failing token
        assert e.args == ('three',)


def test_getitem_nested_through_non_udict():
    ud = udict(one=udict(two=2))
    try:
        ud['one.two.three']
        pytest.fail()
    except KeyError as e:
        assert e.args == ('three',)


def test_getitem_dotted_key():
    ud = udict({'a.b': 2})
    assert ud['a.b'] == 2
    with pytest.raises(KeyError):
        ud['a']


def test_setitem_int_key():
    ud = udict()
    assert 1 not in ud
    ud[1] = 'one'
    assert 1 in ud


def test_setitem_none_key():
    ud = udict()
    ud[None] = 'nope'
    assert len(ud) == 1


def test_setitem_top_level():
    ud = udict()
    ud['one'] = 1
    assert len(ud) == 1


def test_setitem_second_level_existing_first():
    ud = udict()
    ud['one'] = udict()
    ud['one.two'] = 2
    assert len(ud) == 1
    assert ud['one'] == udict(two=2)


def test_setitem_second_level_nonexisting_first():
    ud = udict()
    try:
        ud['one.two'] = 2
        pytest.fail()
    except KeyError as e:
        assert e.args == ('one',)


def test_delitem_top_level_existing():
    ud = udict(one=1)
    del ud['one']
    assert len(ud) == 0
    assert 'one' not in ud


def test_delitem_top_level_nonexisting():
    ud = udict(one=1)
    try:
        del ud['two']
        pytest.fails()
    except KeyError as e:
        assert e.args == ('two',)


def test_delitem_second_level_non_existing_first():
    ud = udict(one=1)
    try:
        del ud['two.three']
        pytest.fails()
    except KeyError as e:
        assert e.args == ('two',)


def test_delitem_second_level_fail_existing_first():
    ud = udict(one=udict(two=2))
    try:
        del ud['one.three']
        pytest.fails()
    except KeyError as e:
        assert e.args == ('three',)


def test_delitem_second_level_success():
    ud = udict(one=udict(two=2, blah=udict(three=3)))
    del ud['one.blah']
    assert 'one' in ud
    assert 'two' in ud['one']
    assert ud == udict(one=udict(two=2))
    del ud['one.two']
    assert ud == udict(one=udict())


def test_delitem_dotted_key():
    d = {'a.b': ''}
    ud = udict(d)
    with pytest.raises(KeyError):
        del ud['a']
    assert ud == udict(d)
    del ud['a.b']
    assert ud == udict()

    d = {'a.b': '', 'a': ''}
    ud = udict(d)
    del ud['a.b']
    assert ud == udict(a='')


def test_pop_present():
    ud = udict(a='a', b='b')
    val = ud.pop('b')
    assert val == 'b'
    ud == udict(a='a')


def test_pop_missing_no_default():
    with pytest.raises(KeyError):
        udict().pop('missing')
    with pytest.raises(KeyError):
        udict(a='aa').pop('aa')


def test_pop_missing_default():
    udict().pop('foo', 'bar') == 'bar'


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
    assert val == 'a.b'
    assert ud['a'] == udict(b='a->b')


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


def test_setattr():
    ud = udict()
    ud.one = 1
    assert len(ud) == 1
    ud.one = udict()
    ud.one.two = 2
    assert ud.one.two == 2
    assert ud['one']['two'] == 2


def test_setattr_dotted_key():
    ud = udict(one=udict(two=2))
    setattr(ud, 'one.two', 3)
    assert ud['one']['two'] == 2
    assert ud['one.two'] == 3


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


def test_delattr_dotted_key():
    orig = udict.fromdict({
        'one': {
            'two': 2
        },
        'one.two': 3
    })
    ud = udict.fromdict(orig)
    del ud['one.two']
    assert 'one.two' in ud
    assert ud['one'] == udict(two=2)


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


def test_fromdict_dotted_key():
    d = {'a.b': ''}
    ud = udict.fromdict(d)
    assert 'a.b' in ud
    assert 'a' not in ud
    assert d == ud
    assert ud == d
    d = {'a.b': 'ab', 'a': {'b': ''}}
    ud = udict.fromdict(d)
    assert 'a.b' in ud
    assert 'a' in ud


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


def test_todict_dotted_keys():
    orig = {
        'one.two': 'dotted',
        'one': {'two': 'nested'}
    }
    ud = udict.fromdict(orig)
    assert isinstance(ud['one'], udict)
    d = ud.todict()
    assert d == orig


def test_keys():
    d = dict(foo=dict(bar='barbar'))
    ud = udict.fromdict(d)
    assert ud.keys()
    assert ud.keys() == d.keys()


def test_keys_dotted():
    d = {'a.b': ''}
    ud = udict(d)
    assert set(ud.keys()) == set(['a.b'])

    ud['a'] = ''
    assert set(ud.keys()) == set(['a.b', 'a'])


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
    assert ud['a.b'] == orig['a.b']
    assert ud['c'] == orig['c']

    ud = udict.fromdict(orig)
    ud.update(udict({'a.b': 'b.a'}))
    assert ud['a.b'] == 'b.a'
    assert ud['a'] == udict(b='a->b')
    assert ud['c'] == 'c'
