Changes
=======

Version 0.4.2 (2017-07-23)
--------------------------

 * doc changes to get description formatted correctly on both github and pypi


Version 0.4.0 (2017-07-23)
--------------------------

 * support python 2.7 and 3.4+, as well as pypy (pypy2 and dev 3.5 pypy)
 * 100% test coverage
 * making available on pypi


Version 0.3.0 (2014-08-09)
--------------------------

 * added support for `dir` method to improve interactive use (exposes stored keys as well as the normal instance and class attributes that would be expected)
 * updates to ensure that `__missing__` is only used from `__getitem__`, and never from methods like `get` or by inadvertently using `__getitem__` from another method
 * more tests


Version 0.2.0 (2014-07-27)
--------------------------

 * main class is now 'uberdict.udict' (was 'uberdict.UberDict')
 * changes to how dotted keys are handled (dots have no special meaning for 'getattr', 'setattr', 'hasattr', 'delattr' but do for 'get' and '__getitem__' and friends)
 * improved README docs and examples
 * more tests
