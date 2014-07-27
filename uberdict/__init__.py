__version__ = '0.1'


class udict(dict):

    """
    A dict that supports attribute-style access and hierarchical keys.

    TODO: add info about key topics such as how dotted keys in a plain
    dict are handled in an udict, how to add a dotted key
    if needed, the relationship between get and getattr with regard
    to dotted keys, etc.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize a new `udict` using `dict.__init__`.

        When passing in a plain dict arg, this won't do any special
        handling of dict values, which will remain plain dicts inside
        the `udict`. For a recursive init that will convert all
        dict values in a dict, use `udict.fromdict`.

        Likewise, dotted keys will not be treated specially, so something
        like `udict({'a.b': 'a.b'})` is equivalent to `ud = udict()` followed
        by `setattr(ud, 'a.b', 'a.b')`.
        """
        super(udict, self).__init__(*args, **kwargs)

    def __getitem__(self, key):
        if not isinstance(key, str) or '.' not in key:
            return dict.__getitem__(self, key)
            # return dict.__getitem__(self, key)
            # return _getitem(self, key)
        tokens = key.split('.')
        obj = self
        for token in tokens:
            try:
                obj = dict.__getitem__(obj, token)
            except TypeError:
                if isinstance(obj, dict) or not hasattr(obj, '__getitem__'):
                    # either it's a dict with no such mapping or a non-dict
                    # that we can't access as if it were a dict
                    raise KeyError(token)
                # a non-dict that could have a mapping
                obj = obj[token]
        return obj

    def __setitem__(self, key, value):
        if not isinstance(key, str) or '.' not in key:
            return super(udict, self).__setitem__(key, value)
        tokens = key.split('.')
        non_terminals, terminal = tokens[:-1], tokens[-1]
        obj = self
        for token in non_terminals:
            # can't automatically create intermediate udicts
            # for missing non-terminal tokens, because it would be
            # impossible to do the same for __setattr__, and
            # consistency across item/attr access styles is more important
            obj = obj[token]
        return super(udict, obj).__setitem__(terminal, value)

    def __delitem__(self, key):
        print('__delitem__:', self, key)
        if not isinstance(key, str) or '.' not in key:
            dict.__delitem__(self, key)
            return

        tokens = key.split('.')
        non_terminals, terminal = tokens[:-1], tokens[-1]
        obj = self
        print('non_terminals:', non_terminals)
        print('terminal:', terminal)
        for token in non_terminals:
            obj = obj[token]
        del obj[terminal]

    def __getattr__(self, key):
        try:
            # no special treatement for dotted keys
            return super(udict, self).__getitem__(key)
        except KeyError as e:
            raise AttributeError("no attribute '%s'" % (e.args[0],))

    def __setattr__(self, key, value):
        # normal setattr behavior, except we put it in the dict
        # instead of setting an attribute (i.e., dotted keys are
        # treated as plain keys)
        super(udict, self).__setitem__(key, value)

    def __delattr__(self, key):
        try:
            # no special special for dotted keys
            super(udict, self).__delitem__(key)
        except KeyError as e:
            raise AttributeError("no attribute '%s'" % (e.args[0]))

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
        tokens = key.split('.')
        non_terminals, terminal = tokens[:-1], tokens[-1]
        obj = self
        try:
            for token in non_terminals:
                obj = dict.__getitem__(obj, token)
        except KeyError:
            if args:
                return args[0]
            raise
        else:
            return dict.pop(obj, terminal, *args)
