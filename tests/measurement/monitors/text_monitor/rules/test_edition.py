# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test widgets used to edit text monitor rules.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from time import sleep

import pytest
import enaml

from exopy.testing.util import process_app_events, handle_dialog
from exopy.measurement.monitors.text_monitor.rules.std_rules import RejectRule

with enaml.imports():
    from exopy.measurement.monitors.text_monitor.rules.edition_views\
         import CreateRuleDialog, EditRulesView


pytest_plugins = str('exopy.testing.measurement.'
                     'monitors.text_monitor.fixtures'),

PLUGIN_ID = 'exopy.measurement.monitors.text_monitor'


@pytest.fixture(params=[True, False])
def should_save(request):
    return request.param


def test_rule_creation_dialog(text_monitor_workbench, dialog_sleep,
                              should_save, monkeypatch):
    """Test the creation of a new rule using the dialog.

    """
    p = text_monitor_workbench.get_plugin(PLUGIN_ID)

    d = CreateRuleDialog(plugin=p)
    d.show()
    process_app_events()
    sleep(dialog_sleep)

    d.central_widget().widgets()[0].selected_tab = \
        'exopy.measurement.monitors.text_monitor.create_rule'
    page = d.central_widget().widgets()[0].pages()[1]
    page_content = page.page_widget().widgets

    # Select rule type
    page_content()[0].selected = 'exopy.RejectRule'
    process_app_events()
    assert d.rule is page.rule
    assert isinstance(page.rule, RejectRule)
    sleep(dialog_sleep)

    # Parametrize rule
    page_content()[1].rule.id = '__dummy'
    page_content()[1].rule.suffixes = ['foo']
    process_app_events()
    sleep(dialog_sleep)

    # Choose whether or not to save: use a parametrization of the test function
    page_content()[-1].checked = should_save
    process_app_events()
    assert isinstance(page.rule, RejectRule)
    sleep(dialog_sleep)

    # Check the created rule
    ok_btn = d.central_widget().widgets()[-2]
    assert ok_btn.enabled
    d.rule.suffixes = []
    with enaml.imports():
        from exopy.measurement.monitors.text_monitor.rules import edition_views

    called = []

    def false_warning(*args, **kwargs):
        called.append(True)

    monkeypatch.setattr(edition_views, 'warning', false_warning)
    ok_btn.clicked = True
    process_app_events()
    assert called

    d.rule.suffixes = ['foo']
    ok_btn.clicked = True
    process_app_events()
    if should_save:
        assert '__dummy' in p.rules


def test_rule_selection_for_loading(text_monitor_workbench, dialog_sleep):
    """Test using the dialog to select an existing config to load a task.

    """
    p = text_monitor_workbench.get_plugin(PLUGIN_ID)

    d = CreateRuleDialog(plugin=p)
    d.show()
    process_app_events()
    sleep(dialog_sleep)

    page = d.central_widget().widgets()[0].pages()[0]
    page_content = page.page_widget().widgets()

    # Select rule config
    qlist = page_content[0]
    qlist.selected_item = qlist.items[-1]
    process_app_events()
    assert page.rule == d.rule
    sleep(dialog_sleep)


def test_rule_edition_dialog(text_monitor_workbench, dialog_sleep):
    """Test editing a rule using the dialog widget.

    """
    p = text_monitor_workbench.get_plugin(PLUGIN_ID)
    m = p.create_monitor(False)
    m.handle_database_entries_change(('added', 'root/test_f', 0))

    d = EditRulesView(monitor=m)
    d.show()
    process_app_events()
    sleep(dialog_sleep)

    # Create a new rule
    psh_btn = d.central_widget().widgets()[-4]

    def create(dial):
        dial.rule = RejectRule(id='__dummy', suffixes=['f'])
    with handle_dialog(custom=create, cls=CreateRuleDialog):
        psh_btn.clicked = True

    assert any([r.id == '__dummy' for r in m.rules])
    assert not m.displayed_entries

    qlist = d.central_widget().widgets()[0]
    qlist.selected_item = [r for r in m.rules if r.id == '__dummy'][0]
    process_app_events()
    assert d.central_widget().widgets()[1].rule
    sleep(dialog_sleep)

    # Save rule and save and add to default
    try:
        psh_btn = d.central_widget().widgets()[-2]
        act = psh_btn.children[0].children[0]
        act.triggered = True
        process_app_events()
        assert '__dummy' in p.rules
        assert '__dummy' not in p.default_rules
        del p._user_rules['__dummy']

        act = psh_btn.children[0].children[1]
        act.triggered = True
        process_app_events()
        assert '__dummy' in p.rules
        assert '__dummy' in p.default_rules

    finally:
        if '__dummy' in p._user_rules:
            del p._user_rules['__dummy']

    # Delete rule
    psh_btn = d.central_widget().widgets()[-3]
    psh_btn.clicked = True
    process_app_events()
    assert '__dummy' not in m.rules
    assert m.displayed_entries

    d.central_widget().widgets()[-1].clicked = True
    process_app_events()
