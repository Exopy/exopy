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

import logging
from contextlib import contextmanager
from collections import defaultdict
from threading import RLock, Lock

from atom.api import Atom, Instance, Value, Int


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

        yield self

        self._lock.release()

    def get(self, key, default=None):
        """Equivalent of dict.get but lock protected.

        """
        with self._lock:
            aux = self._dict.get(key, default)

        return aux

    def items(self):
        """Equivalent of dict.items but lock protected.

        """
        with self.locked():
            for item in self._dict.items():
                yield item

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

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


class ResourceHolder(SharedDict):
    """Base class for storing resources and handling releases and restting.

    """

    def release(self):
        """Release the resources held by this container.

        This method should be safe to call on already released resources.

        """
        raise NotImplementedError()

    def reset(self):
        """Reset the resources.

        This is different from releasing. This method is typically called when
        resuming a measure to ensure that the state of the resources can be
        trusted inspite of the interruption.

        """
        pass


class ThreadPoolResource(ResourceHolder):
    """Resource holder specialized to handle threads grouped in pools.

    """
    def __init__(self, default=list):
        super(ThreadPoolResource, self).__init__(default)

    def release(self):
        """Join all the threads still alive.

        """
        for _, pool in self.items():
            for thread in pool:
                try:
                    thread.join()
                except Exception:
                    log = logging.getLogger(__name__)
                    mes = 'Failed to join thread %s from pool %s'
                    log.exception(mes, thread, pool)


class InstrsResource(ResourceHolder):
    """Resource holder specialized to handle instruments.

    Each driver instance should be stored as a 2-tuple with its associated
    starter. (driver, starter)

    """
    def release(self):
        """Finalize all the opened connections.

        """
        for instr_profile in self:
            try:
                driver, starter = self[instr_profile]
                starter.finalize(driver)
            except Exception:
                log = logging.getLogger(__name__)
                mes = 'Failed to close connection to instr : %s'
                log.exception(mes, self[instr_profile])

    def reset(self):
        """Clean the cache of all drivers to avoid corrupted value due to
        user interferences.

        """
        for instr_id in self:
            d, starter = self[instr_id]
            starter.reset(d)


class FilesResource(ResourceHolder):
    """Resource holder specialized in handling standard file descriptors.

    """
    def release(self):
        """Close all the opened files.

        """
        for file_id in self:
            try:
                self[file_id].close()
            except Exception:
                log = logging.getLogger(__name__)
                mes = 'Failed to close file handler : %s'
                log.exception(mes, self[file_id])
