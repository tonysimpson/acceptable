# Copyright 2019 Canonical Ltd.  This software is licensed under the
# GNU Lesser General Public License version 3 (see the file LICENSE).
from __future__ import print_function
from future import standard_library

standard_library.install_aliases()
import sys
from mock import MagicMock
from importlib import import_module


class DummyFinder(object):
    """Implements PEP 302 module finder and loader which will pretend to
    load modules but actually just create mocks that look like them.

    This allows python code to be loaded when its dependencies are not
    installed.

    allowed_real_modules is a list of module names to not mock instead the
    module finders are tried.

    modules in allowed_real_modules will raise the correct error on import if
    they can't be loaded.

    This class is used by DummyImporterContext which patches sys.modules
    and sys.meta_path.
    """

    def __init__(self, allowed_real_modules):
        self.allowed = set(allowed_real_modules)

    def find_module(self, fullname, path=None):
        if fullname in self.allowed:
            return None
        else:
            return self

    def load_module(self, fullname):
        try:
            return sys.modules[fullname]
        except KeyError:
            pass
        mod = MagicMock()
        sys.modules[fullname] = mod
        mod.__name__ = fullname
        mod.__file__ = "<Dummy>"
        mod.__loader__ = self
        if "." not in fullname:
            mod.__path__ = [fullname]
        mod.__package__ = None
        mod.__doc__ = "Dummy"
        return mod


class DummyImporterContext(object):
    """Creates a context in which modules, other than those in
    allowed_real_modules, will not be imported but instead replaced with
    mocks.

    Manager sys.modules so that the mock modules are removed after
    the context ends.

    Allows python code to be imported and executed even when its
    dependencies are not installed.
    """

    def __init__(self, *allowed_real_modules):
        self.allowed_real_modules = set(allowed_real_modules)

    def __enter__(self):
        self.orig_sys_modules = sys.modules
        self.finder = DummyFinder(self.allowed_real_modules)
        sys.modules = dict(sys.modules)
        sys.meta_path.insert(0, self.finder)

    def __exit__(self, *args):
        sys.meta_path.remove(self.finder)
        sys.modules = self.orig_sys_modules
