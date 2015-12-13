# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
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

from ecpy.measure.monitors.text_monitor.rules.std_rules import FormatRule
from ecpy.testing.util import set_preferences

with enaml.imports():
    from .contributed_rules import RulesManifest

pytest_plugins = str('ecpy.testing.measure.monitors.text_monitor.fixtures')


@pytest.fixture
def text_monitor_plugin(text_monitor_workbench):
    """Create a text monitor with some interesting preferences.

    """
    conf = {}
    path = 'ecpy.measure.monitors.text_monitor'
    rule1 = {'class_id': 'ecpy.FormatRule', 'id': 'test_format',
             'suffixes': repr(['a', 'b']),
             'new_entry_formatting': '{a}/{b}',
             'new_entry_suffix': 'c'}
    rule2 = {'class_id': 'ecpy.RejectRule',
             'id': 'test_reject',
             'suffixes': repr(['a', 'b'])}
    conf[path] = {'_user_rules': repr({'test_format': rule1,
                                       'test_reject': rule2}),
                  'default_rules': repr(['test_format', 'unknown'])}
    set_preferences(text_monitor_workbench, conf)
    p = text_monitor_workbench.get_plugin('ecpy.measure.monitors.text_monitor')
    return p


def test_lifecycle(text_monitor_plugin):
    """Test that starting and stopping the plugin have the expected
    consequences.

    """
    assert 'test_format' in text_monitor_plugin.rules
    assert 'test_reject' in text_monitor_plugin.rules
    assert 'ecpy.FormatRule' in text_monitor_plugin.rule_types
    assert 'ecpy.RejectRule' in text_monitor_plugin.rule_types

    manifest = RulesManifest()
    text_monitor_plugin.workbench.register(manifest)

    assert 'contributed' in text_monitor_plugin.rules
    assert 'tests.Contributed' in text_monitor_plugin.rule_types

    text_monitor_plugin.stop()

    assert not text_monitor_plugin.rules
    assert not text_monitor_plugin.rule_types


def test_plugin_build_rule(text_monitor_plugin):
    """ Test building a rule.

    """
    config = {'class_id': 'ecpy.RejectRule',
              'id': 'test_reject',
              'suffixes': repr(['a', 'b'])}
    rule = text_monitor_plugin.build_rule(config)

    assert rule.id == 'test_reject'
    assert rule.suffixes == ['a', 'b']
    assert rule.__class__.__name__ == 'RejectRule'

    rule = text_monitor_plugin.build_rule('test_format')

    assert rule.id == 'test_format'

    rule_name = text_monitor_plugin._rule_configs.contributions.keys()[0]
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
    assert rule_conf == {'class_id': 'ecpy.FormatRule',
                         'id': 'Test',
                         'description': '',
                         'hide_entries': 'True',
                         'suffixes': repr(['loop', 'index']),
                         'new_entry_suffix': 'progress',
                         'new_entry_formatting': '{index}/{loop}'}
