# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the behavior of the standard rules.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest

from ecpy.measure.monitors.text_monitor.rules.std_rules import (RejectRule,
                                                                FormatRule)

pytest_plugins = str('ecpy.testing.measure.monitors.text_monitor.fixtures'),


@pytest.fixture
def monitor(text_monitor_workbench):
    """Text with some entries.

    """
    p = text_monitor_workbench.get_plugin('ecpy.measure.monitors.text_monitor')
    m = p.create_monitor(False)
    m.handle_database_change(('added', 'root/test_value', 0))
    m.handle_database_change(('added', 'root/test_index', 0))
    m.handle_database_change(('added', 'root/test_number', 0))
    return m


def test_reject_rule(monitor):
    """Test rejecting an entry.

    """
    r = RejectRule(suffixes=['value'])

    r.try_apply('root/test_index', monitor)
    assert len(monitor.displayed_entries) == 3

    r.try_apply('root/test_value', monitor)
    assert len(monitor.displayed_entries) == 2
    assert monitor.undisplayed_entries[0].path == 'root/test_value'

    r.try_apply('root/test_number', monitor)
    assert len(monitor.displayed_entries) == 2


def test_format_rule(monitor):
    """Test simplifying some entries through formatting.

    """
    f = FormatRule(suffixes=['index', 'number'], new_entry_suffix='progress',
                   new_entry_formatting='{index}/{number}')

    f.try_apply('root/test_value', monitor)
    assert len(monitor.displayed_entries) == 3

    f.try_apply('root/test_index', monitor)
    assert len(monitor.displayed_entries) == 2
    assert len(monitor.hidden_entries) == 2

    f.hide_entries = False

    monitor.handle_database_change(('added', 'root/simp/test_index', 0))
    f.try_apply('root/simp/test_index', monitor)
    assert len(monitor.displayed_entries) == 3

    monitor.handle_database_change(('added', 'root/simp/test_number', 0))
    f.try_apply('root/simp/test_number', monitor)
    assert len(monitor.displayed_entries) == 5
    assert len(monitor.hidden_entries) == 2


def test_reject_rule_editor(monitor):
    """
    """
    pass
    # Test editing suffix


def test_format_rule_editor(monitor):
    """
    """
    pass
    # Test adding filtering suffix

    # Test editing filtering suffix

    # Test deleting filtering suffix

    # Set new suffix

    # Set new formatting
