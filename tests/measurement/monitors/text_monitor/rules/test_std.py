# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the behavior of the standard rules.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from time import sleep

import pytest
import enaml

from exopy.measurement.monitors.text_monitor.rules.std_rules\
     import RejectRule, FormatRule
from exopy.testing.util import process_app_events

with enaml.imports():
    from exopy.measurement.monitors.text_monitor.rules.std_views\
        import SuffixesValidator, RejectRuleView, FormatRuleView
    from exopy.testing.windows import ContainerTestingWindow


pytest_plugins = str('exopy.testing.measurement.'
                     'monitors.text_monitor.fixtures'),


@pytest.fixture
def plugin(text_monitor_workbench):
    """Text monitor plugin.

    """
    p = text_monitor_workbench.get_plugin(
        'exopy.measurement.monitors.text_monitor')
    return p


@pytest.fixture
def monitor(plugin):
    """Text with some entries.

    """
    m = plugin.create_monitor(False)
    m.handle_database_entries_change(('added', 'root/test_value', 0))
    m.handle_database_entries_change(('added', 'root/test_index', 0))
    m.handle_database_entries_change(('added', 'root/test_number', 0))
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

    monitor.handle_database_entries_change(('added', 'root/simp/test_index',
                                            0))
    f.try_apply('root/simp/test_index', monitor)
    assert len(monitor.displayed_entries) == 3

    monitor.handle_database_entries_change(('added', 'root/simp/test_number',
                                            0))
    f.try_apply('root/simp/test_number', monitor)
    assert len(monitor.displayed_entries) == 5
    assert len(monitor.hidden_entries) == 2


def test_suffixes_validator():
    """Test that the regex does validate only strings that can be seen as lists

    """
    v = SuffixesValidator()
    assert v.validate('e, e_e, e1, r_1')
    assert not v.validate('e, ')
    assert not v.validate('e, /')


def test_reject_rule_editor(windows, plugin, dialog_sleep):
    """Test editing a reject rule.

    """
    r = RejectRule(suffixes=['foo', 'bar'])
    w = RejectRuleView(plugin=plugin, rule=r)

    window = ContainerTestingWindow(widget=w)
    window.show()
    process_app_events()
    assert w.widgets()[-1].text == 'foo, bar'
    sleep(dialog_sleep)

    w.widgets()[-1].text = 'bar'
    process_app_events()
    assert r.suffixes == ['bar']
    sleep(dialog_sleep)

    r.suffixes = ['foo']
    process_app_events()
    assert w.widgets()[-1].text == 'foo'
    sleep(dialog_sleep)

    w.widgets()[-1].text = 'bar, foo, barfoo'
    process_app_events()
    assert r.suffixes == ['bar', 'foo', 'barfoo']
    sleep(dialog_sleep)

    assert w.validate()[0]
    r.suffixes = []
    assert not w.validate()[0]


def test_format_rule_editor(windows, plugin, dialog_sleep):
    """Test editing a format rule.

    """
    r = FormatRule(suffixes=['foo', 'bar'], new_entry_suffix='barfoo',
                   new_entry_formatting='{bar}/{foo}')
    w = FormatRuleView(plugin=plugin, rule=r)

    # Test editing suffixes
    window = ContainerTestingWindow(widget=w)
    window.show()
    process_app_events()
    widget = w.widgets()[-6]
    assert widget.text == 'foo, bar'
    sleep(dialog_sleep)

    widget.text = 'bar'
    process_app_events()
    assert r.suffixes == ['bar']
    sleep(dialog_sleep)

    r.suffixes = ['foo']
    process_app_events()
    assert widget.text == 'foo'
    sleep(dialog_sleep)

    widget.text = 'bar, foo, barfoo'
    process_app_events()
    assert r.suffixes == ['bar', 'foo', 'barfoo']
    sleep(dialog_sleep)

    # Set new suffix
    widget = w.widgets()[-4]
    assert widget.text == 'barfoo'
    widget.text = 'foobar'
    process_app_events()
    assert r.new_entry_suffix == 'foobar'
    sleep(dialog_sleep)

    # Set new formatting
    widget = w.widgets()[-2]
    assert widget.text == '{bar}/{foo}'
    widget.text = '{foo}/{bar}'
    process_app_events()
    assert r.new_entry_formatting == '{foo}/{bar}'
    sleep(dialog_sleep)

    # Set hide entries
    widget = w.widgets()[-1]
    assert widget.checked
    widget.checked = False
    process_app_events()
    assert not r.hide_entries
    sleep(dialog_sleep)

    # Test validate function
    r.suffixes = ['foo', 'bar']
    assert w.validate()[0]
    r.suffixes = []
    assert not w.validate()[0]
    r.suffixes = ['foo', 'bar']
    assert w.validate()

    r.new_entry_suffix = ''
    assert not w.validate()[0]
    r.new_entry_suffix = 'foobar'
    assert w.validate()[0]

    r.new_entry_formatting = '{foo}'
    assert not w.validate()[0]
