# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Thread safe bit flag with convenient interface.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from threading import Event, RLock


class BitFlag(object):
    """Bit flag conveniency class providing thread safety facilities.

    Parameters
    ----------
    flags : iterable[unicode]
        Name of the flags that this flag understand.

    """

    __slots__ = ('flags', '_lock', '_flags', '_events', '_state')

    def __new__(cls, flags):

        self = object.__new__(cls)
        self.flags = flags
        self._flags = {f: 2**i for i, f in enumerate(flags)}
        self._events = {}
        self._lock = RLock()
        self._state = 0

    def set(self, *flags):
        """Set specified flags.

        If a flag is already set this is a no-op. If a thread is waiting on a
        flag, it gets notified.

        """
        with self._lock:
            for f in flags:
                self._state |= self._flags[f]
                if f in self._events:
                    self._events[f].set()
                    del self._events[f]

    def clear(self, *flags):
        """Clear the specified flags.

        If a flag is already cleared this is a no-op. If a thread is waiting
        on a flag clearing, it gets notified.

        """
        with self._lock:
            for f in flags:
                self._state &= ~self._flags[f]

    def test(self, *flags):
        """Test is all specified flags are set.

        """
        res = False
        with self._lock:
            for f in flags:
                res &= self._state & f

        return res

    def wait(self, timeout, *flags):
        """Wait till some flags are set.

        Parameters
        ----------

        timeout : float|None
            Maximum time to wait. If None waits forever.

        flags : iterable[unicode]
            Flags upon which to wait.

        Returns
        -------
        result : bool
            False if the method returned because of the timeout.

        """
        events = []
        with self._lock:
            for f in flags:
                if not self.test(f):
                    if f not in self._events:
                        self._events[f] = Event()
                    events = self._events[f]

        res = True
        for e in events:
            res &= e.wait(timeout)

        return res
