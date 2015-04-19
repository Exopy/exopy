# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Thread safe object to use in tasks.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Atom, Instance, Value, Int
from contextlib import contextmanager
from collections import defaultdict
from threading import RLock, Lock


class SharedCounter(Atom):
    """ Thread-safe counter object.

    """
    #: Current count of the counter. User should not manipulate this directly.
    count = Int()

    def increment(self):
        """Increment the counter by one.

        """
        with self._lock:
            self.count += 1

    def decrement(self):
        """Decrement the counter by one.

        """
        with self._lock:
            self.count += -1

    #: Simple lock to ensure the thread safety of operations.
    _lock = Value(factory=Lock)


class SharedDict(Atom):
    """ Dict wrapper using a lock to protect access to its values.

    Parameters
    ----------
    default : callable, optional
        Callable to use as argument for defaultdict, if unspecified a regular
        dict is used.

    """
    def __init__(self, default=None):
        super(SharedDict, self).__init__()
        if default is not None:
            self._dict = defaultdict(default)
        else:
            self._dict = {}

    @contextmanager
    def safe_access(self, key):
        """Context manager to safely manipulate a value of the dict.

        """
        lock = self._lock
        lock.acquire()

        yield self._dict[key]

        lock.release()

    @contextmanager
    def locked(self):
        """Acquire the instance lock.

        """
        self._lock.acquire()

        yield

        self._lock.release()

    def get(self, key, default=None):
        with self._lock:
            aux = self._dict.get(key, default)

        return aux

    #: Underlying dict.
    _dict = Instance((dict, defaultdict))

    #: Re-entrant lock use to secure the access to the dict.
    _lock = Value(factory=RLock)

    def __getitem__(self, key):

        with self.locked():
            aux = self._dict[key]

        return aux

    def __setitem__(self, key, value):

        with self._lock:
            self._dict[key] = value

    def __delitem__(self, key):

        with self._lock:
            del self._dict[key]

    def __contains__(self, key):
        return key in self._dict

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)
