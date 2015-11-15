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

import os

import pytest
from enaml.workbench.api import Workbench
from configobj import ConfigObj

from ecpy.measure.monitors.text_monitor.rules.std_rules import FormatRule


@pytest.fixture
def text_monitor_workbench(measure_workbench):
    """Alter the preferences so that we get pre-defined rules.

    """



@pytest.mark.usefixture('measure_plugin')
class TestPlugin(object):

    test_dir = ''

    @classmethod
    def setup_class(cls):
        # Creating dummy directory for prefs (avoid prefs interferences).
        directory = os.path.dirname(__file__)
        cls.test_dir = os.path.join(directory, '_temps')
        create_test_dir(cls.test_dir)

        # Creating dummy default.ini file in utils.
        util_path = os.path.join(directory, '..', '..', '..', 'hqc_meas',
                                 'utils', 'preferences')
        def_path = os.path.join(util_path, 'default.ini')

        # Making the preference manager look for info in test dir.
        default = ConfigObj(def_path)
        default['folder'] = cls.test_dir
        default['file'] = 'default_test.ini'
        default.write()

        conf = ConfigObj(os.path.join(cls.test_dir, 'default_test.ini'))
        path = u'hqc_meas.measurement.monitors.text_monitor'
        prefs = {'manifests': repr([(path, 'TextMonitorManifest')])}
        conf[u'hqc_meas.measure'] = prefs
        path = u'hqc_meas.measure.monitors.text_monitor'
        rule1 = {'class_name': 'FormatRule', 'name': 'test_format',
                 'suffixes': repr(['a', 'b']),
                 'new_entry_formatting': '{a}/{b}',
                 'new_entry_suffix': 'c'}
        rule2 = {'class_name': 'RejectRule',
                 'name': 'test_reject',
                 'suffixes': repr(['a', 'b'])}
        conf[path] = {'rules': repr({'rule1': rule1, 'rule2': rule2}),
                      'default_rules': repr(['rule1'])}

        conf.write()

    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(UIManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(PreferencesManifest())
        self.workbench.register(LogManifest())
        self.workbench.register(MeasureManifest())

        # Needed otherwise the monitor manifest is not registered.
        self.workbench.get_plugin(u'hqc_meas.measure')

    def teardown(self):
        self.workbench.unregister(u'hqc_meas.measure')
        self.workbench.unregister(u'hqc_meas.logging')
        self.workbench.unregister(u'hqc_meas.preferences')
        self.workbench.unregister(u'hqc_meas.state')
        self.workbench.unregister(u'enaml.workbench.ui')
        self.workbench.unregister(u'enaml.workbench.core')

    def test_plugin_build_rule(self):
        """ Test building a rule.

        """
        config = {'class_name': 'RejectRule',
                  'name': 'test_reject',
                  'suffixes': repr(['a', 'b'])}
        id_pl = u'hqc_meas.measure.monitors.text_monitor'
        plugin = self.workbench.get_plugin(id_pl)
        rule = plugin.build_rule(config)

        assert_equal(rule.name, 'test_reject')
        assert_equal(rule.suffixes, ['a', 'b'])
        assert_equal(rule.__class__.__name__, 'RejectRule')

        assert_is(plugin.build_rule({'class_name': None}), None)

    def test_plugin_create_monitor1(self):
        """ Test creating a default monitor using the plugin.

        """
        id_pl = u'hqc_meas.measure.monitors.text_monitor'
        plugin = self.workbench.get_plugin(id_pl)
        monitor = plugin.create_monitor()

        assert_equal(monitor._plugin, plugin)
        assert_true(monitor.declaration)
        assert_true(monitor.rules)
        rule = monitor.rules[0]
        assert_equal(rule.__class__.__name__, 'FormatRule')
        assert_equal(rule.name, 'test_format')
        assert_equal(rule.suffixes, ['a', 'b'])
        assert_equal(rule.new_entry_formatting, '{a}/{b}')
        assert_equal(rule.new_entry_suffix, 'c')

    def test_plugin_create_monitor(self):
        """ Test creating a raw monitor using the plugin.

        """
        id_pl = u'hqc_meas.measure.monitors.text_monitor'
        plugin = self.workbench.get_plugin(id_pl)
        monitor = plugin.create_monitor(raw=True)

        assert_equal(monitor._plugin, plugin)
        assert_true(monitor.declaration)
        assert_false(monitor.rules)

    def test_monitor_set_state(self):
        """ Test restoring the state of a monitor.

        """
        id_pl = u'hqc_meas.measure.monitors.text_monitor'
        plugin = self.workbench.get_plugin(id_pl)
        monitor = plugin.create_monitor(raw=True)
        monitor.measure_name = 'Test'
        monitor.auto_show = False
        entry = monitor._create_default_entry('test', 1)
        entry.name = 'Custom'
        entry.path = 'custom'
        entry.formatting = 'This test n {root/test_loop}*{root/test2_loop}'
        entry.depend_on = ['root/test_loop', 'root/test2_loop']
        monitor.custom_entries.append(entry)

        rule = FormatRule(name='Test', suffixes=['loop', 'index'],
                          new_entry_suffix='progress',
                          new_entry_formatting='{index}/{loop}')
        monitor.rules.append(rule)

        monitor.database_modified({'value': ('root/test_loop', 10)})
        monitor.database_modified({'value': ('root/test2_index', 1)})
        monitor.database_modified({'value': ('root/test_index', 1)})
        monitor.database_modified({'value': ('root/test2_loop', 10)})

        state = monitor.get_state()
        # Atom issue of _DictProxy
        values = dict(monitor._database_values)

        monitor_rebuilt = plugin.create_monitor(raw=True)
        monitor_rebuilt.set_state(state, values)
        assert_equal(monitor_rebuilt.measure_name, 'Test')
        assert_false(monitor.auto_show)

        assert_true(monitor_rebuilt.custom_entries)
        c_entry = monitor_rebuilt.custom_entries[0]
        assert_equal(c_entry.name, entry.name)
        assert_equal(c_entry.path, entry.path)
        assert_equal(c_entry.formatting, entry.formatting)
        assert_equal(c_entry.depend_on, entry.depend_on)

        assert_true(monitor_rebuilt.rules)
        c_rule = monitor_rebuilt.rules[0]
        assert_equal(c_rule.name, rule.name)
        assert_equal(c_rule.suffixes, rule.suffixes)
        assert_equal(c_rule.new_entry_suffix, rule.new_entry_suffix)
        assert_equal(c_rule.new_entry_formatting, rule.new_entry_formatting)

        assert_equal(len(monitor_rebuilt.displayed_entries), 3)
        assert_equal(len(monitor_rebuilt.undisplayed_entries), 0)
        assert_equal(len(monitor_rebuilt.hidden_entries), 4)

    def test_add_rule_to_plugin(self):
        """ Test adding a new rule definition to a plugin.

        """
        id_pl = u'hqc_meas.measure.monitors.text_monitor'
        plugin = self.workbench.get_plugin(id_pl)
        monitor = plugin.create_monitor()

        rule = FormatRule(name='Test', suffixes=['loop', 'index'],
                          new_entry_suffix='progress',
                          new_entry_formatting='{index}/{loop}')
        monitor.rules.append(rule)

        monitor.add_rule_to_plugin('rule1')
        assert_equal(len(plugin.rules.keys()), 2)

        monitor.add_rule_to_plugin('Test')
        assert_equal(len(plugin.rules.keys()), 3)
        assert_in('Test', plugin.rules)
        rule_conf = plugin.rules['Test']
        assert_dict_equal(rule_conf, {'class_name': 'FormatRule',
                                      'name': 'Test',
                                      'hide_entries': 'True',
                                      'suffixes': repr(['loop', 'index']),
                                      'new_entry_suffix': 'progress',
                                      'new_entry_formatting': '{index}/{loop}'}
                          )
