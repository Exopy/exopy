# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the widget used to create/edit a custom entry.

"""
import pytest
import enaml

from exopy.measurement.monitors.text_monitor.entry import MonitoredEntry
from exopy.testing.util import wait_for_window_displayed, wait_for_destruction

with enaml.imports():
    from exopy.measurement.monitors.text_monitor.custom_entry_edition\
        import EntryDialog


@pytest.fixture
def monitor(text_monitor_workbench):
    """Bare text monitor as created by the plugin.

    """
    p = text_monitor_workbench.get_plugin(
        'exopy.measurement.monitors.text_monitor')
    m = p.create_monitor(False)
    m.handle_database_entries_change(('added', 'root/test', 0))
    m.handle_database_entries_change(('added', 'root/simp/test', 0))
    m.handle_database_entries_change(('added', 'root/comp/test', 0))
    return m


def test_creating_new_custom_entry(monitor, exopy_qtbot, dialog_sleep):
    """Test creating an  entry using the dialog.

    """
    d = EntryDialog(monitor=monitor)
    d.show()
    wait_for_window_displayed(exopy_qtbot, d)
    exopy_qtbot.wait(dialog_sleep)

    w = d.central_widget().widgets()
    w[1].text = 'test'
    exopy_qtbot.wait(10 + dialog_sleep)

    w[5].text = '{root/test}, {simp/test}, {comp/test}'
    exopy_qtbot.wait(10 + dialog_sleep)

    b = d.builder
    for e in ('root/test', 'simp/test', 'comp/test'):
        assert e in b.map_entries
    b.add_entry(0, 'after')
    assert b.used_entries
    exopy_qtbot.wait(10 + dialog_sleep)

    b.used_entries[0].entry = 'root/test'
    exopy_qtbot.wait(10 + dialog_sleep)

    b.add_entry(0, 'after')
    assert not b.used_entries[-1].entry
    exopy_qtbot.wait(10 + dialog_sleep)

    b.used_entries[-1].entry = 'simp/test'
    exopy_qtbot.wait(10 + dialog_sleep)

    b.add_entry(0, 'before')
    assert not b.used_entries[0].entry
    exopy_qtbot.wait(10 + dialog_sleep)

    b.used_entries[0].entry = 'comp/test'
    exopy_qtbot.wait(10 + dialog_sleep)

    w[-2].clicked = True

    def assert_entry():
        assert d.entry
    exopy_qtbot.wait_until(assert_entry)

    e = d.entry
    assert e.name == 'test'
    assert (sorted(e.depend_on) ==
            sorted(('root/test', 'root/simp/test', 'root/comp/test')))

    d.close()
    wait_for_destruction(exopy_qtbot, d)


def test_editing_cusom_entry(monitor, exopy_qtbot, dialog_sleep):
    """Test that we can edit an existing monitored entry.

    """
    e = MonitoredEntry(name='test', path='test',
                       depend_on=['root/test', 'root/simp/test',
                                  'root/comp/test'],
                       formatting=('{root/test}, {root/simp/test}, '
                                   '{root/comp/test}')
                       )

    # Test cancelling after editon.
    d = EntryDialog(monitor=monitor, entry=e)
    d.show()
    wait_for_window_displayed(exopy_qtbot, d)
    exopy_qtbot.wait(dialog_sleep)

    w = d.central_widget().widgets()
    assert w[1].text == 'test'
    w[1].text = 'dummy'
    exopy_qtbot.wait(10 + dialog_sleep)

    w[-1].clicked = True

    def assert_name():
        assert d.entry.name == 'test'
    exopy_qtbot.wait_until(assert_name)

    # Test doing some actuel editions
    d = EntryDialog(monitor=monitor, entry=e)
    d.show()
    exopy_qtbot.wait(10 + dialog_sleep)

    w = d.central_widget().widgets()
    w[1].text = 'test2'
    exopy_qtbot.wait(10 + dialog_sleep)

    w[5].text = '{simp/test}, {comp/test}'
    exopy_qtbot.wait(10 + dialog_sleep)

    b = d.builder
    assert b.used_entries[0].entry == 'root/test'
    b.remove_entry(0)
    exopy_qtbot.wait(10 + dialog_sleep)

    w[-2].clicked = True

    def assert_name():
        e = d.entry
        assert e.name == 'test2'
        assert (sorted(e.depend_on) ==
                sorted(('root/simp/test', 'root/comp/test')))
    exopy_qtbot.wait_until(assert_name)
