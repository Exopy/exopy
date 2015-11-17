# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the behavior of the RuleType declarator.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
import enaml
from atom.api import Atom, Dict, List

from ecpy.measure.monitors.text_monitor.rules.base import (Rules, RuleType,
                                                           BaseRule)


class _DummyCollector(Atom):

    contributions = Dict()

    _delayed = List()


@pytest.fixture
def collector():
    return _DummyCollector()


def test_building_class_id():
    """Test building the class id of a rule.

    """
    r = BaseRule()
    assert r.class_id == 'ecpy.BaseRule'


PATH = 'ecpy.measure.monitors.text_monitor.rules'


@pytest.fixture
def rule_decl():
    return RuleType(
        rule=PATH + '.std_rules:RejectRule',
        view=PATH + '.std_views:RejectRuleView')


def test_register_rule_decl1(collector, rule_decl):
    """Test registering the root task.

    """
    tb = {}
    parent = Rules(group='test',
                   path='ecpy.measure.monitors.text_monitor.rules')
    parent.insert_children(None, [rule_decl])
    rule_decl.rule = 'std_rules:RejectRule'
    rule_decl.view = 'std_views:RejectRuleView'
    parent.register(collector, tb)
    infos = collector.contributions['ecpy.RejectRule']
    from ecpy.measure.monitors.text_monitor.rules.std_rules import RejectRule
    with enaml.imports():
        from ecpy.measure.monitors.text_monitor.rules.std_views\
            import RejectRuleView
    assert infos.cls is RejectRule
    assert infos.view is RejectRuleView


def test_register_rule_decl_path_1(collector, rule_decl):
    """Test handling wrong path : missing ':'.

    Such an errors can't be detected till the pass on the delayed and the
    dead-end is detected.

    """
    tb = {}
    rule_decl.rule = 'ecpy.tasks'
    rule_decl.register(collector, tb)
    assert 'Error 0' in tb


def test_register_rule_decl_path_2(collector, rule_decl):
    """Test handling wrong path : too many ':'.

    """
    tb = {}
    rule_decl.view = 'ecpy.tasks:tasks:Task'
    rule_decl.register(collector, tb)
    assert 'ecpy.RejectRule' in tb


def test_register_rule_decl_duplicate1(collector, rule_decl):
    """Test handling duplicate : in collector.

    """
    collector.contributions['ecpy.RejectRule'] = None
    tb = {}
    rule_decl.rule = 'ecpy.tasks:RejectRule'
    rule_decl.register(collector, tb)
    assert 'ecpy.RejectRule_duplicate1' in tb


def test_register_rule_decl_duplicate2(collector, rule_decl):
    """Test handling duplicate : in traceback.

    """
    tb = {'ecpy.RejectRule': 'rr'}
    rule_decl.register(collector, tb)
    assert 'ecpy.RejectRule_duplicate1' in tb


def test_register_rule_decl_taskcls1(collector, rule_decl):
    """Test handling task class issues : failed import no such module.

    """
    tb = {}
    rule_decl.rule = 'ecpy.tasks.foo:Rule'
    rule_decl.register(collector, tb)
    assert 'ecpy.Rule' in tb and 'import' in tb['ecpy.Rule']


def test_register_rule_decl_taskcls1_bis(collector, rule_decl):
    """Test handling task class issues : failed import error while importing.

    """
    tb = {}
    rule_decl.rule = 'ecpy.testing.broken_module:Rule'
    rule_decl.register(collector, tb)
    assert 'ecpy.Rule' in tb and 'NameError' in tb['ecpy.Rule']


def test_register_rule_decl_taskcls2(collector, rule_decl):
    """Test handling task class issues : undefined in module.

    """
    tb = {}
    rule_decl.rule = PATH + ':Rule'
    rule_decl.register(collector, tb)
    assert 'ecpy.Rule' in tb and 'attribute' in tb['ecpy.Rule']


def test_register_rule_decl_taskcls3(collector, rule_decl):
    """Test handling task class issues : wrong type.

    """
    tb = {}
    rule_decl.rule = 'ecpy.tasks.tools.database:TaskDatabase'
    rule_decl.register(collector, tb)
    assert 'ecpy.TaskDatabase' in tb and 'subclass' in tb['ecpy.TaskDatabase']


def test_register_rule_decl_view1(collector, rule_decl):
    """Test handling view issues : failed import no such module.

    """
    tb = {}
    rule_decl.view = PATH + ':RuleView'
    rule_decl.register(collector, tb)
    assert 'ecpy.RejectRule' in tb and 'import' in tb['ecpy.RejectRule']


def test_register_rule_decl_view1_bis(collector, rule_decl):
    """Test handling view issues : failed import error while importing.

    """
    tb = {}
    rule_decl.view = 'ecpy.testing.broken_enaml:Rule'
    rule_decl.register(collector, tb)
    assert 'ecpy.RejectRule' in tb and 'NameError' in tb['ecpy.RejectRule']


def test_register_rule_decl_view2(collector, rule_decl):
    """Test handling view issues : undefined in module.

    """
    tb = {}
    rule_decl.view = PATH + '.std_views:RejectRule'
    rule_decl.register(collector, tb)
    assert 'ecpy.RejectRule' in tb and 'attribute' in tb['ecpy.RejectRule']


def test_register_rule_decl_view3(collector, rule_decl):
    """Test handling view issues : wrong type.

    """
    tb = {}
    rule_decl.view = 'ecpy.tasks.tools.database:TaskDatabase'
    rule_decl.register(collector, tb)
    assert 'ecpy.RejectRule' in tb and 'subclass' in tb['ecpy.RejectRule']


def test_unregister_rule_decl1(collector, rule_decl):
    """Test unregistering a rule.

    """
    rule_decl.is_registered = True
    rule_decl.register(collector, {})
    rule_decl.unregister(collector)
    assert not collector.contributions


def test_unregister_rule_decl2(collector, rule_decl):
    """Test unregistering a rule which already disappeared.

    """
    rule_decl.register(collector, {})
    collector.contributions = {}
    rule_decl.unregister(collector)
    # Would raise an error if the error was not properly catched.


def test_str_ruele(rule_decl):
    """Test string representation.

    """
    str(rule_decl)
