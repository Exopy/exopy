# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the MonitoredEntry class.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from exopy.measurement.monitors.text_monitor.entry import MonitoredEntry
from exopy.testing.util import process_app_events


def test_entry_formatting():
    """Test that we can correctly format an entry.

    """
    e = MonitoredEntry(name='test', formatting='{a} = {b}',
                       depend_on=['a', 'b'])

    e.update(dict(a=1, b=2, c=3))
    process_app_events()
    assert e.value == '1 = 2'
