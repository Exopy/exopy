# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
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

from exopy.measure.monitors.text_monitor.rules.base import (Rules, RuleType,
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
    assert r.class_id == 'exopy.BaseRule'


PATH = 'exopy.measure.monitors.text_monitor.rules'


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
                   path='exopy.measure.monitors.text_monitor.rules')
    parent.insert_children(None, [rule_decl])
    rule_decl.rule = 'std_rules:RejectRule'
    rule_decl.view = 'std_views:RejectRuleView'
    parent.register(collector, tb)
    infos = collector.contributions['exopy.RejectRule']
    from exopy.measure.monitors.text_monitor.rules.std_rules import RejectRule
    with enaml.imports():
        from exopy.measure.monitors.text_monitor.rules.std_views\
            import RejectRuleView
    assert infos.cls is RejectRule
    assert infos.view is RejectRuleView


def test_register_rule_decl_path_1(collector, rule_decl):
    """Test handling wrong path : missing ':'.

    Such an errors can't be detected till the pass on the delayed and the
    dead-end is detected.

    """
    tb = {}
    rule_decl.rule = 'exopy.tasks'
    rule_decl.register(collector, tb)
    assert 'Error 0' in tb


def test_register_rule_decl_path_2(collector, rule_decl):
    """Test handling wrong path : too many ':'.

    """
    tb = {}
    rule_decl.view = 'exopy.tasks:tasks:Task'
    rule_decl.register(collector, tb)
    assert 'exopy.RejectRule' in tb


def test_register_rule_decl_duplicate1(collector, rule_decl):
    """Test handling duplicate : in collector.

    """
    collector.contributions['exopy.RejectRule'] = None
    tb = {}
    rule_decl.rule = 'exopy.tasks:RejectRule'
    rule_decl.register(collector, tb)
    assert 'exopy.RejectRule_duplicate1' in tb


def test_register_rule_decl_duplicate2(collector, rule_decl):
    """Test handling duplicate : in traceback.

    """
    tb = {'exopy.RejectRule': 'rr'}
    rule_decl.register(collector, tb)
    assert 'exopy.RejectRule_duplicate1' in tb


def test_register_rule_decl_taskcls1(collector, rule_decl):
    """Test handling task class issues : failed import no such module.

    """
    tb = {}
    rule_decl.rule = 'exopy.tasks.foo:Rule'
    rule_decl.register(collector, tb)
    assert 'exopy.Rule' in tb and 'import' in tb['exopy.Rule']


def test_register_rule_decl_taskcls1_bis(collector, rule_decl):
    """Test handling task class issues : failed import error while importing.

    """
    tb = {}
    rule_decl.rule = 'exopy.testing.broken_module:Rule'
    rule_decl.register(collector, tb)
    assert 'exopy.Rule' in tb and 'NameError' in tb['exopy.Rule']


def test_register_rule_decl_taskcls2(collector, rule_decl):
    """Test handling task class issues : undefined in module.

    """
    tb = {}
    rule_decl.rule = PATH + ':Rule'
    rule_decl.register(collector, tb)
    assert 'exopy.Rule' in tb and 'attribute' in tb['exopy.Rule']


def test_register_rule_decl_taskcls3(collector, rule_decl):
    """Test handling task class issues : wrong type.

    """
    tb = {}
    rule_decl.rule = 'exopy.tasks.tasks.database:TaskDatabase'
    rule_decl.register(collector, tb)
    assert 'exopy.TaskDatabase' in tb and 'subclass' in tb['exopy.TaskDatabase']


def test_register_rule_decl_view1(collector, rule_decl):
    """Test handling view issues : failed import no such module.

    """
    tb = {}
    rule_decl.view = PATH + ':RuleView'
    rule_decl.register(collector, tb)
    assert 'exopy.RejectRule' in tb and 'import' in tb['exopy.RejectRule']


def test_register_rule_decl_view1_bis(collector, rule_decl):
    """Test handling view issues : failed import error while importing.

    """
    tb = {}
    rule_decl.view = 'exopy.testing.broken_enaml:Rule'
    rule_decl.register(collector, tb)
    assert 'exopy.RejectRule' in tb and 'NameError' in tb['exopy.RejectRule']


def test_register_rule_decl_view2(collector, rule_decl):
    """Test handling view issues : undefined in module.

    """
    tb = {}
    rule_decl.view = PATH + '.std_views:RejectRule'
    rule_decl.register(collector, tb)
    assert 'exopy.RejectRule' in tb and 'attribute' in tb['exopy.RejectRule']


def test_register_rule_decl_view3(collector, rule_decl):
    """Test handling view issues : wrong type.

    """
    tb = {}
    rule_decl.view = 'exopy.tasks.tasks.database:TaskDatabase'
    rule_decl.register(collector, tb)
    assert 'exopy.RejectRule' in tb and 'subclass' in tb['exopy.RejectRule']


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


def test_str_rule(rule_decl):
    """Test string representation.

    """
    str(rule_decl)
