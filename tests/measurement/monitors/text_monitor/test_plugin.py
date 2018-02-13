# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the plugin in charge of the text monitor preferences and extensions
mechanisms.


"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
import enaml

from exopy.measurement.monitors.text_monitor.rules.std_rules import FormatRule
from exopy.testing.util import set_preferences

with enaml.imports():
    from .contributed_rules import RulesManifest

pytest_plugins = str('exopy.testing.measurement.'
                     'monitors.text_monitor.fixtures')


@pytest.fixture
def text_monitor_plugin(text_monitor_workbench):
    """Create a text monitor with some interesting preferences.

    """
    conf = {}
    path = 'exopy.measurement.monitors.text_monitor'
    rule1 = {'class_id': 'exopy.FormatRule', 'id': 'test_format',
             'suffixes': repr(['a', 'b']),
             'new_entry_formatting': '{a}/{b}',
             'new_entry_suffix': 'c'}
    rule2 = {'class_id': 'exopy.RejectRule',
             'id': 'test_reject',
             'suffixes': repr(['a', 'b'])}
    conf[path] = {'_user_rules': repr({'test_format': rule1,
                                       'test_reject': rule2}),
                  'default_rules': repr(['test_format', 'unknown'])}
    set_preferences(text_monitor_workbench, conf)
    p = text_monitor_workbench.get_plugin(
        'exopy.measurement.monitors.text_monitor')
    # Set manually as we added those without the preferences.
    p.default_rules = ['test_format', 'unknown']
    return p


def test_lifecycle(text_monitor_plugin):
    """Test that starting and stopping the plugin have the expected
    consequences.

    """
    assert 'test_format' in text_monitor_plugin.rules
    assert 'test_reject' in text_monitor_plugin.rules
    assert 'exopy.FormatRule' in text_monitor_plugin.rule_types
    assert 'exopy.RejectRule' in text_monitor_plugin.rule_types

    manifest = RulesManifest()
    text_monitor_plugin.workbench.register(manifest)

    assert 'contributed' in text_monitor_plugin.rules
    assert 'measurement.Contributed' in text_monitor_plugin.rule_types

    text_monitor_plugin.stop()

    assert not text_monitor_plugin.rules
    assert not text_monitor_plugin.rule_types


def test_handling_missing_default_rule(text_monitor_workbench, caplog):
    """Test that default rules not backed by a config are discarded.

    """
    conf = {}
    path = 'exopy.measurement.monitors.text_monitor'
    conf[path] = {'default_rules': repr(['test_format', 'unknown'])}
    set_preferences(text_monitor_workbench, conf)
    text_monitor_workbench.get_plugin(
        'exopy.measurement.monitors.text_monitor')
    assert caplog.records


def test_plugin_build_rule(text_monitor_plugin):
    """ Test building a rule.

    """
    config = {'class_id': 'exopy.RejectRule',
              'id': 'test_reject',
              'suffixes': repr(['a', 'b'])}
    rule = text_monitor_plugin.build_rule(config)

    assert rule.id == 'test_reject'
    assert rule.suffixes == ['a', 'b']
    assert rule.__class__.__name__ == 'RejectRule'

    rule = text_monitor_plugin.build_rule('test_format')

    assert rule.id == 'test_format'

    rule_name = list(text_monitor_plugin._rule_configs.contributions)[0]
    rule = text_monitor_plugin.build_rule(rule_name)
    assert rule.id == rule_name

    assert text_monitor_plugin.build_rule('__unknown__') is None

    config = {'class_id': '__unknown__',
              'id': 'test_reject',
              'suffixes': repr(['a', 'b'])}
    assert text_monitor_plugin.build_rule(config) is None


def test_plugin_get_rule_type(text_monitor_plugin):
    """Test getting the class associated to a rule type.

    """
    assert text_monitor_plugin.get_rule_type(text_monitor_plugin.rule_types[0])


def test_plugin_get_rule_view(text_monitor_plugin):
    """Test getting the class associated to a rule type.

    """
    r = text_monitor_plugin.build_rule('test_format')
    assert text_monitor_plugin.get_rule_view(r)


def test_plugin_create_default_monitor(text_monitor_plugin):
    """ Test creating a default monitor using the plugin.

    """
    monitor = text_monitor_plugin.create_monitor(default=True)

    assert monitor._plugin is text_monitor_plugin
    assert monitor.declaration
    assert monitor.rules
    rule = monitor.rules[0]
    assert rule.__class__.__name__ == 'FormatRule'
    assert rule.id == 'test_format'
    assert rule.suffixes == ['a', 'b']
    assert rule.new_entry_formatting == '{a}/{b}'
    assert rule.new_entry_suffix == 'c'


def test_plugin_create_bare_monitor(text_monitor_plugin):
    """ Test creating a raw monitor using the plugin.

    """
    monitor = text_monitor_plugin.create_monitor(default=False)

    assert monitor._plugin is text_monitor_plugin
    assert monitor.declaration
    assert not monitor.rules


def test_plugin_save_rule(text_monitor_plugin):
    """Test adding a new rule definition to a plugin.

    """

    rule = FormatRule(id='Test', suffixes=['loop', 'index'],
                      new_entry_suffix='progress',
                      new_entry_formatting='{index}/{loop}')

    text_monitor_plugin.save_rule(rule)

    assert 'Test' in text_monitor_plugin.rules
    rule_conf = text_monitor_plugin._user_rules['Test']
    assert rule_conf == {'class_id': 'exopy.FormatRule',
                         'id': 'Test',
                         'description': '',
                         'hide_entries': 'True',
                         'suffixes': repr(['loop', 'index']),
                         'new_entry_suffix': 'progress',
                         'new_entry_formatting': '{index}/{loop}'}
