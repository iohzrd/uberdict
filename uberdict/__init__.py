__version__ = '0.1'


class UberDict(dict):

    def __init__(self, *args, **kwargs):
        """
        Initialize a new `UberDict` using `dict.__init__`.

        When passing in a plain dict arg, this won't do any special
        handling of dict values, which will remain plain dicts inside
        the `UberDict`. For a recursive init that will convert all
        dict values in a dict, use `UberDict.fromdict`.
        """
        super(UberDict, self).__init__(*args, **kwargs)

    def __getitem__(self, key):
        try:
            return super(UberDict, self).__getitem__(key)
        except KeyError:
            if not isinstance(key, str) or '.' not in key:
                raise
            tokens = key.split('.')
            obj = self
            for token in tokens:
                if not isinstance(obj, dict):
                    raise KeyError(token)
                obj = super(UberDict, obj).__getitem__(token)
            return obj

    def __setitem__(self, key, value):
        if not isinstance(key, str) or '.' not in key:
            super(UberDict, self).__setitem__(key, value)
        else:
            tokens = key.split('.')
            non_terminals, terminal = tokens[:-1], tokens[-1]
            obj = self
            for token in non_terminals:
                # can't automatically create intermediate UberDicts
                # for missing non-terminal tokens, because it would be
                # impossible to do the same for __setattr__, and
                # consistency across item/attr access styles is more important
                obj = obj[token]
            super(UberDict, obj).__setitem__(terminal, value)

    def __delitem__(self, key):
        if '.' not in key:
            super(UberDict, self).__delitem__(key)
        else:
            tokens = key.split('.')
            non_terminals, terminal = tokens[:-1], tokens[-1]
            obj = self
            for token in non_terminals:
                child = obj.get(token)
                if child is None:
                    # TODO: may want to distinguish between a
                    # None in the bag and no such item
                    raise KeyError(token)
                obj = child
            super(UberDict, obj).__delitem__(terminal)

    def __getattr__(self, key):
        try:
            return self.__getitem__(key)
        except KeyError as e:
            raise AttributeError("no attribute '%s'" % (e.args[0],))

    def __setattr__(self, key, value):
        super(UberDict, self).__setitem__(key, value)

    def __delattr__(self, key):
        try:
            self.__delitem__(key)
        except KeyError as e:
            raise AttributeError("no attribute '%s'" % (e.args[0]))

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    @classmethod
    def fromkeys(self, seq, value=None):
        return UberDict((elem, value) for elem in seq)

    @classmethod
    def fromdict(cls, mapping):
        """
        Create a new `UberDict` from the given `mapping` dict.

        The resulting `UberDict` will be equivalent to the input
        `mapping` dict but with all dict instances (recursively)
        converted to an `UberDict` instance.  If you don't want
        this behavior (you want sub-dicts to remain plain dicts),
        use `UberDict(my_dict)` instead.
        """
        ud = cls()
        for k in mapping:
            v = mapping[k]  # py2/py3
            if isinstance(v, dict) and not isinstance(v, cls):
                v = cls.fromdict(v)
            ud[k] = v
        return ud

    def todict(self):
        """
        Create a plain `dict` from this `UberDict`.

        The resulting `dict` will be equivalent to this `UberDict`
        but with all `UberDict` instances (recursively) converted to
        a plain `dict` instance.
        """
        d = dict()
        for k in self:
            v = self[k]  # py2/py3
            if isinstance(v, UberDict):
                v = v.todict()
            d[k] = v
        return d

    def copy(self):
        """
        Return a shallow copy of this `UberDict`.

        For a deep copy, use `UberDict.fromdict` (as long as there aren't
        plain dict values that you don't want converted to `UberDict`).
        """
        return UberDict(self)

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
