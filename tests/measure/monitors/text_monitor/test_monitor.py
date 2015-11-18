# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the behavior of the text monitor.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest

from ecpy.measure.monitors.text_monitor.rules.std_rules import (FormatRule,
                                                                RejectRule)
from ecpy.testing.util import process_app_events

pytest_plugins = str('ecpy.testing.measure.monitors.text_monitor.fixtures'),


@pytest.fixture
def monitor(text_monitor_workbench):
    """Bare text monitor as created by the plugin.

    """
    p = text_monitor_workbench.get_plugin('ecpy.measurr')
    return p.create('monitor', 'ecpy.Text monitor', False)


def test_create_default_entry(monitor):
    """ Test creating an entryt from a path.

    """
    entry = monitor._create_default_entry('test/entry_test', 1)
    assert entry.path == 'test/entry_test'
    assert entry.name == 'entry_test'
    assert entry.formatting == '{test/entry_test}'
    assert entry.depend_on == ['test/entry_test']
    assert entry.value == '1'


def test_adding_removing_moving_entries(monitor):
    """Test adding an entry to the displayed ones.

    """
    entry = monitor._create_default_entry('test/entry_test', 1)
    monitor.add_entries('displayed', [entry])

    assert entry in monitor.displayed_entries
    assert monitor.updaters == {'test/entry_test': [entry.update]}
    assert monitor.monitored_entries == ['test/entry_test']

    entry2 = monitor._create_default_entry('test/entry_test2', 1)
    monitor.add_entries('undisplayed', [entry])

    assert monitor.updaters == {'test/entry_test': [entry.update]}
    assert monitor.monitored_entries == ['test/entry_test']

    monitor.move_entries('undisplayed', 'displayed', [entry2])

    assert 'test/entry_test2' in monitor.updaters
    assert 'test/entry_test2' in monitor.monitored_entries

    monitor.remove_entries('displayed', [entry2])

    assert 'test/entry_test2' not in monitor.updaters
    assert 'test/entry_test2' not in monitor.monitored_entries

    with pytest.raises(ValueError):
        monitor.add_entries('', ())

    with pytest.raises(ValueError):
        monitor.remove_entries('', ())

    with pytest.raises(ValueError):
        monitor.move_entries('', 'displayed', ())

    with pytest.raises(ValueError):
        monitor.move_entries('displayed', '', ())


def test_handle_database_change1(monitor):
    """ Test handling the adding of an entry to the database.

    """
    monitor.handle_database_change(('added', 'test/entry_test', 1))

    assert monitor.monitored_entries == ['test/entry_test']
    assert len(monitor.displayed_entries) == 1
    assert not monitor.undisplayed_entries
    assert not monitor.hidden_entries
    entry = monitor.displayed_entries[0]
    assert entry.path == 'test/entry_test'
    assert entry.name == 'entry_test'
    assert entry.formatting == '{test/entry_test}'
    assert entry.depend_on == ['test/entry_test']
    assert monitor._database_values == {'test/entry_test': 1}
    assert 'test/entry_test' in monitor.updaters


def test_handle_database_change2(monitor):
    """ Test handling the adding of an entry subject to a reject rule.

    """
    monitor.rules.append(RejectRule(id='Test', suffixes=['test']))
    monitor.handle_database_change(('added', 'root/make_test', 1))

    assert monitor.monitored_entries == []
    assert not monitor.displayed_entries
    assert len(monitor.undisplayed_entries) == 1
    assert not monitor.hidden_entries
    assert monitor.undisplayed_entries[0].depend_on == ['root/make_test']
    assert monitor._database_values == {'root/make_test': 1}
    assert not monitor.updaters


def test_handle_database_change3(app, monitor):
    """ Test handling the adding of entries subject to a format rule.

    """
    rule = FormatRule(id='Test', suffixes=['loop', 'index'],
                      new_entry_suffix='progress',
                      new_entry_formatting='{index}/{loop}')
    monitor.rules.append(rule)
    monitor.handle_database_change(('added', 'root/test_loop', 10))

    assert monitor.monitored_entries == ['root/test_loop']
    assert len(monitor.displayed_entries) == 1
    assert not monitor.undisplayed_entries
    assert not monitor.hidden_entries
    assert monitor.displayed_entries[0].depend_on == ['root/test_loop']
    assert monitor._database_values == {'root/test_loop': 10}
    assert 'root/test_loop' in monitor.updaters

    monitor.handle_database_change(('added', 'root/test2_index', 1))

    assert (monitor.monitored_entries == ['root/test_loop',
                                          'root/test2_index'])
    assert len(monitor.displayed_entries) == 2
    assert not monitor.undisplayed_entries
    assert not monitor.hidden_entries
    assert (monitor._database_values == {'root/test_loop': 10,
                                         'root/test2_index': 1})

    monitor.handle_database_change(('added', 'root/test_index', 1))

    assert (monitor.monitored_entries == ['root/test_loop',
                                          'root/test2_index',
                                          'root/test_index'])
    assert len(monitor.displayed_entries) == 2
    assert not monitor.undisplayed_entries
    assert len(monitor.hidden_entries) == 2
    assert (monitor._database_values == {'root/test_loop': 10,
                                         'root/test2_index': 1,
                                         'root/test_index': 1})
    assert len(monitor.updaters['root/test_loop']) == 1
    assert len(monitor.updaters['root/test_index']) == 1

    entry = monitor.displayed_entries[0]
    if entry.name != 'test_progress':
        entry = monitor.displayed_entries[1]

    assert entry.name == 'test_progress'
    assert entry.path == 'root/test_progress'
    assert entry.depend_on == ['root/test_loop', 'root/test_index']
    assert entry.formatting == '{root/test_index}/{root/test_loop}'
    entry.update(monitor._database_values)
    process_app_events()
    assert entry.value == '1/10'

    rule.hide_entries = False
    monitor.handle_database_change(('added', 'root/test2_loop', 10))
    assert (monitor.monitored_entries == ['root/test_loop',
                                          'root/test2_index',
                                          'root/test_index',
                                          'root/test2_loop'])
    assert len(monitor.displayed_entries) == 4
    assert not monitor.undisplayed_entries
    assert len(monitor.hidden_entries) == 2
    assert (monitor._database_values == {'root/test_loop': 10,
                                         'root/test2_index': 1,
                                         'root/test_index': 1,
                                         'root/test2_loop': 10})
    assert len(monitor.updaters['root/test2_loop']) == 2
    assert len(monitor.updaters['root/test2_index']) == 2


def test_handle_database_change4(monitor):
    """ Test handling the adding/removing an entry linked to a custom one.

    """
    entry = monitor._create_default_entry('dummy/test', 1)
    entry.name = 'Custom'
    entry.path = 'custom'
    entry.formatting = 'This test n {root/test}'
    entry.depend_on = ['root/test']
    monitor.custom_entries.append(entry)

    monitor.handle_database_change(('added', 'root/aux', 1))

    assert monitor.monitored_entries == ['root/aux']
    assert len(monitor.displayed_entries) == 1
    assert not monitor.undisplayed_entries
    assert not monitor.hidden_entries
    assert monitor._database_values == {'root/aux': 1}

    monitor.handle_database_change(('added', 'root/test', 2))

    assert monitor.monitored_entries == ['root/aux', 'root/test']
    assert len(monitor.displayed_entries) == 3
    assert not monitor.undisplayed_entries
    assert not monitor.hidden_entries
    assert monitor._database_values == {'root/aux': 1, 'root/test': 2}
    assert len(monitor.updaters['root/test']) == 2

    monitor.handle_database_change(('removed', 'root/test',))
    assert monitor.monitored_entries == ['root/aux']
    assert len(monitor.displayed_entries) == 1
    assert not monitor.undisplayed_entries
    assert not monitor.hidden_entries
    assert monitor._database_values == {'root/aux': 1}
    assert monitor.custom_entries
    assert 'root/test' not in monitor.updaters


def test_refresh_monitored_entries(monitor):
    """ Test refreshing entries (with a custom entry).

    """
    entry = monitor._create_default_entry('dummy/test', 1)
    entry.name = 'Custom'
    entry.path = 'custom'
    entry.formatting = 'This test n {test}'
    entry.depend_on = ['root/test']
    monitor.custom_entries.append(entry)

    monitor.handle_database_change(('added', 'root/test', 1))
    monitor.refresh_monitored_entries({'root/test': 2})

    assert monitor.monitored_entries == ['root/test']
    assert len(monitor.displayed_entries) == 2
    assert not monitor.undisplayed_entries
    assert not monitor.hidden_entries
    assert monitor._database_values == {'root/test': 2}

    monitor._database_values = {'root/aux': 2}
    monitor.refresh_monitored_entries()
    assert monitor.monitored_entries == ['root/aux']
    assert len(monitor.displayed_entries) == 1
    assert not monitor.undisplayed_entries
    assert not monitor.hidden_entries


def test_process_news(monitor):
    """ Test processing news coming from a database.

    """
    rule = FormatRule(id='Test', suffixes=['loop', 'index'],
                      new_entry_suffix='progress',
                      new_entry_formatting='{index}/{loop}',
                      hide_entries=False)
    monitor.rules.append(rule)
    monitor.handle_database_change(('added', 'root/test_loop', 10))
    monitor.handle_database_change(('added', 'root/test_index', 1))

    monitor.process_news(('root/test_index', 2))
    process_app_events()
    assert monitor.displayed_entries[0].value == '10'
    assert monitor.displayed_entries[1].value == '2'
    assert monitor.displayed_entries[2].value == '2/10'


def test_clear_state(monitor):
    """ Test clearing the monitor state.

    """
    rule = FormatRule(id='Test', suffixes=['loop', 'index'],
                      new_entry_suffix='progress',
                      new_entry_formatting='{index}/{loop}')
    monitor.rules.append(rule)
    monitor.handle_database_change(('added', 'root/test_loop', 10))
    monitor.handle_database_change(('added', 'root/test2_index', 1))
    monitor.handle_database_change(('added', 'root/test_index', 1))

    monitor._clear_state()
    assert not monitor.displayed_entries
    assert not monitor.undisplayed_entries
    assert not monitor.hidden_entries
    assert not monitor.updaters
    assert not monitor.custom_entries
    assert not monitor.monitored_entries


def test_get_set_state(monitor, monkeypatch):
    """ Test get_state.

    """
    entry = monitor._create_default_entry('root/test', 1)
    entry.name = 'Custom'
    entry.path = 'custom'
    entry.formatting = 'This test n {root/test_loop}*{root/test2_loop}'
    entry.depend_on = ['root/test_loop', 'root/test2_loop']
    monitor.custom_entries.append(entry)

    rule = FormatRule(id='Test', suffixes=['loop', 'index'],
                      new_entry_suffix='progress',
                      new_entry_formatting='{index}/{loop}')
    monitor.rules.append(rule)

    monitor.handle_database_change(('added', 'root/test_loop', 10))
    monitor.handle_database_change(('added', 'root/test2_index', 1))
    monitor.handle_database_change(('added', 'root/test_index', 1))
    monitor.handle_database_change(('added', 'root/test2_loop', 10))

    state = monitor.get_state()

    assert 'rule_0' in state
    rule = state['rule_0']
    assert (rule == {'class_id': 'ecpy.FormatRule', 'id': 'Test',
                     'description': '',
                     'hide_entries': 'True',
                     'suffixes': "[u'loop', u'index']",
                     'new_entry_suffix': 'progress',
                     'new_entry_formatting': '{index}/{loop}'})

    assert 'custom_0' in state
    custom = state['custom_0']
    aux = {'name': 'Custom', 'path': 'custom',
           'formatting': 'This test n {root/test_loop}*{root/test2_loop}',
           'depend_on': "[u'root/test_loop', u'root/test2_loop']"}
    assert custom == aux

    assert (state['displayed'] ==
            repr([e.path for e in monitor.displayed_entries]))
    assert (state['undisplayed'] ==
            repr([e.path for e in monitor.undisplayed_entries]))
    assert (state['hidden'] ==
            repr([e.path for e in monitor.hidden_entries]))

    monitor._clear_state()
    import ecpy.measure.monitors.text_monitor.monitor as mod
    monkeypatch.setattr(mod, 'information', lambda *args, **kwargs: None)
    monitor.set_state(state, {'root/test_loop': 10, 'root/test2_index': 1,
                              'root/test_index': 1, 'root/test2_loop': 10,
                              'root/r': 1})

    assert monitor.rules
    assert monitor.rules[0].id == 'Test'
    assert (sorted([e.path for e in monitor.displayed_entries]) ==
            sorted(['custom', 'root/test_progress', 'root/test2_progress',
                    'root/r']))


def test_known_monitored_entries(monitor):
    """ Test all_database_entries property.

    """
    test = {'test': 1, '2': 'aux'}
    monitor._database_values = test
    assert sorted(monitor.known_monitored_entries) == sorted(test)


# XXXX
def test_edition_window(text_monitor_workbench):
    """Test the capabalities of the widget used to edit a text monitor.

    """
    p = text_monitor_workbench.get_plugin('ecpy.measure.monitors.text_monitor')
    m = p.create_monitor(False)
    # Need to apply a format rule
    m.handle_database_change(('added', 'root/test', 0))
    m.handle_database_change(('added', 'root/simp/test', 0))
    m.handle_database_change(('added', 'root/comp/test', 0))
    # Need a custom entry
    return m

    # Test hide all

    # Test show one

    # Test hide one

    # Test hide all

    # Test show hidden

    # Test edit rules

    # Test add entry

    # Test edit entry

    # Test delete entry


def test_text_monitor_item(test_monitor_workbench, monitor, measure):
    """Test that the dock item of the text monitor does display the right
    entries.

    """
    # Check only displayed entries are indeed shown.
