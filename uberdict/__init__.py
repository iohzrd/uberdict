__version__ = '0.2'

ALL = ['udict']

import sys

# TODO: add support for __missing__


class udict(dict):

    """
    A dict that supports attribute-style access and hierarchical keys.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize a new `udict` using `dict.__init__`.

        When passing in a dict arg, this won't do any special
        handling of values that are dicts. They will remain plain dicts inside
        the `udict`. For a recursive init that will convert all
        dict values in a dict to udicts, use `udict.fromdict`.

        Likewise, dotted keys will not be treated specially, so something
        like `udict({'a.b': 'a.b'})` is equivalent to `ud = udict()` followed
        by `setattr(ud, 'a.b', 'a.b')`.
        """
        dict.__init__(self, *args, **kwargs)

    def __getitem__(self, key):
        if not isinstance(key, str) or '.' not in key:
            try:
                return dict.__getitem__(self, key)
            except KeyError:
                raise
        obj, token = _descend(self, key)
        return _get(obj, token)

    def __setitem__(self, key, value):
        if not isinstance(key, str) or '.' not in key:
            return dict.__setitem__(self, key, value)

        obj, token = _descend(self, key)
        return dict.__setitem__(obj, token, value)

    def __delitem__(self, key):
        if not isinstance(key, str) or '.' not in key:
            dict.__delitem__(self, key)
            return
        obj, token = _descend(self, key)
        del obj[token]

    def __getattr__(self, key):
        try:
            # no special treatement for dotted keys
            return dict.__getitem__(self, key)
        except KeyError as e:
            raise AttributeError("no attribute '%s'" % (e.args[0],))

    def __setattr__(self, key, value):
        # normal setattr behavior, except we put it in the dict
        # instead of setting an attribute (i.e., dotted keys are
        # treated as plain keys)
        dict.__setitem__(self, key, value)

    def __delattr__(self, key):
        try:
            # no special handling of dotted keys
            dict.__delitem__(self, key)
        except KeyError as e:
            raise AttributeError("no attribute '%s'" % (e.args[0]))

    def __reduce__(self):
        # pickle the contents of a udict as a list of items;
        # __getstate__ and __setstate__ aren't needed
        constructor = self.__class__
        instance_args = (list(iteritems(self)),)
        return constructor, instance_args

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    @classmethod
    def fromkeys(self, seq, value=None):
        return udict((elem, value) for elem in seq)

    @classmethod
    def fromdict(cls, mapping):
        """
        Create a new `udict` from the given `mapping` dict.

        The resulting `udict` will be equivalent to the input
        `mapping` dict but with all dict instances (recursively)
        converted to an `udict` instance.  If you don't want
        this behavior (you want sub-dicts to remain plain dicts),
        use `udict(my_dict)` instead.
        """
        ud = cls()
        for k in mapping:
            v = dict.__getitem__(mapping, k)  # okay for py2/py3
            if isinstance(v, dict):
                v = cls.fromdict(v)
            dict.__setitem__(ud, k, v)
        return ud

    def todict(self):
        """
        Create a plain `dict` from this `udict`.

        The resulting `dict` will be equivalent to this `udict`
        but with all `udict` instances (recursively) converted to
        a plain `dict` instance.
        """
        d = dict()
        for k in self:
            v = dict.__getitem__(self, k)
            if isinstance(v, udict):
                v = v.todict()
            d[k] = v
        return d

    def copy(self):
        """
        Return a shallow copy of this `udict`.

        For a deep copy, use `udict.fromdict` (as long as there aren't
        plain dict values that you don't want converted to `udict`).
        """
        return udict(self)

    def setdefault(self, key, default=None):
        """
        If `key` is in the dictionary, return its value.
        If not, insert `key` with a value of `default` and return `default`,
        which defaults to `None`.
        """
        try:
            return self[key]
        except KeyError:
            self[key] = default
            return default

    def __contains__(self, key):
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True

    def pop(self, key, *args):
        if not isinstance(key, str) or '.' not in key:
            return dict.pop(self, key, *args)
        try:
            obj, token = _descend(self, key)
        except KeyError:
            if args:
                return args[0]
            raise
        else:
            return dict.pop(obj, token, *args)


# py2/py3 compatibility
if sys.version_info[0] == 2:
    def iteritems(d):
        return d.iteritems()
else:
    def iteritems(d):
        return d.items()


# helper to do careful and consistent `obj[name]`
def _get(obj, name):
    """
    Get the indexable value with given `name` from `obj`, which may be
    a `dict` (or subclass) or a non-dict that has a `__getitem__` method.
    """
    try:
        # try to get value using dict's __getitem__ descriptor first
        return dict.__getitem__(obj, name)
    except TypeError:
        # if it's a dict, then preserve the TypeError
        if isinstance(obj, dict):
            raise
        # otherwise try one last time, relying on __getitem__ if any
        return obj[name]


# helper for common use case of traversing a path like 'a.b.c.d'
# to get the 'a.b.c' object and do something to it with the 'd' token
def _descend(obj, key):
    """
    Descend on `obj` by splitting `key` on '.' (`key` must contain at least
    one '.') and using `get` on each token that results from splitting
    to fetch the successive child elements, stopping on the next-to-last.

     A `__getitem__` would do `dict.__getitem__(value, token)` with the
     result, and a `__setitem__` would do `dict.__setitem__(value, token, v)`.

    :returns:
    (value, token) - `value` is the next-to-last object found, and
    `token` is the last token in the `key` (the only one that wasn't consumed
    yet).


    """
    tokens = key.split('.')
    assert len(tokens) > 1
    value = obj
    for token in tokens[:-1]:
        value = _get(value, token)
    return value, tokens[-1]
