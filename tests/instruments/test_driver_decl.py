# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the driver declarator.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
from atom.api import Atom, Dict

from ecpy.instruments.drivers.driver_decl import Drivers, Driver


class _DummyCollector(Atom):

    contributions = Dict()


@pytest.fixture
def collector():
    return _DummyCollector()


def make_decl(members):
    d = Driver(driver='tests.instruments.false_driver:FalseDriver',
               model='E8257D')
    for m, v in members:
        parent = Drivers(**{m: v})
        d.set_parent(parent)
        d = parent

    return d


DEFAULT_MEMBERS = (('architecture', 'lantz'), ('manufacturer', 'Keysight'),
                   ('serie', 'PSG'), ('starter', 'lantz'),
                   ('kind', 'RF source'),
                   ('connections', {'visa_tcpip': {}}),
                   ('settings', {'lantz': {}}))


@pytest.fixture
def driver_decl():
    d = make_decl(DEFAULT_MEMBERS)

    return d


def test_register_driver_decl1(collector, driver_decl):
    """Test registering the a driver.

    """
    tb = {}
    driver_decl.register(collector, tb)

    assert not tb
    assert len(collector.contributions) == 1
    d = collector.contributions['tests.lantz.FalseDriver']
    for m, v in DEFAULT_MEMBERS:
        try:
            assert getattr(d, m) == v
        except AttributeError:
            assert d.infos[m] == v


def test_handling_missing_non_required_members(collector):
    """Test registering a driver without values for the non-required members.

    """
    tb = {}
    m = dict(DEFAULT_MEMBERS)
    del m['serie']
    del m['kind']
    del m['settings']
    decl = make_decl(m.items())
    decl.register(collector, tb)
    assert not tb
    assert len(collector.contributions) == 1
    d = collector.contributions['tests.lantz.FalseDriver']
    for m, v in (('kind', 'Other'), ('serie', ''), ('settings', {})):
        try:
            assert getattr(d, m) == v
        except AttributeError:
            assert d.infos[m] == v


def test_handling_missing_non_required_members2(collector):
    """Test registering a driver without values for the non-required members.

    Case in which the declarator has no parent.

    """
    tb = {}
    m = dict(DEFAULT_MEMBERS)
    del m['serie']
    del m['kind']
    del m['settings']
    decl = Driver(driver='tests.instruments.false_driver:FalseDriver',
                  model='E8257D', parent=None, **m)
    decl.register(collector, tb)
    assert not tb
    assert len(collector.contributions) == 1
    d = collector.contributions['tests.lantz.FalseDriver']
    for m, v in (('kind', 'Other'), ('serie', ''), ('settings', {})):
        try:
            assert getattr(d, m) == v
        except AttributeError:
            assert d.infos[m] == v


def test_overriding_parent_member_in_decl(collector, driver_decl):
    """Test that the value set in the Driver override the parent value.

    """
    d = list(driver_decl.traverse())[-1]
    d.manufacturer = 'Agilent'

    tb = {}
    driver_decl.register(collector, tb)

    assert not tb
    assert len(collector.contributions) == 1
    d = collector.contributions['tests.lantz.FalseDriver']
    assert d.infos['manufacturer'] == 'Agilent'


def test_handling_missing_architecture(collector):
    """Test handlign a missing architecture which prevents to build the id.

    """
    tb = {}
    m = dict(DEFAULT_MEMBERS)
    del m['architecture']
    decl = make_decl(m.items())
    decl.register(collector, tb)
    assert 'tests.instruments.false_driver:FalseDriver' in tb


def test_handling_missing_required_member(collector):
    """Test handlign a missing required member.

    """
    tb = {}
    m = dict(DEFAULT_MEMBERS)
    del m['manufacturer']
    decl = make_decl(m.items())
    decl.register(collector, tb)
    assert 'tests.lantz.FalseDriver' in tb


def test_register_driver_decl_path_1(collector, driver_decl):
    """Test handling wrong path : missing ':'.

    """
    tb = {}
    d = list(driver_decl.traverse())[-1]
    d.driver = 'ecpy.tasks'
    driver_decl.register(collector, tb)
    assert 'ecpy.tasks' in tb


def test_register_driver_decl_duplicate1(collector, driver_decl):
    """Test handling duplicate : in collector.

    """
    collector.contributions['tests.lantz.FalseDriver'] = None
    tb = {}
    driver_decl.register(collector, tb)
    assert 'tests.lantz.FalseDriver_duplicate1' in tb


def test_register_driver_decl_duplicate2(collector, driver_decl):
    """Test handling duplicate : in traceback.

    """
    tb = {'tests.lantz.FalseDriver': 'rr'}
    driver_decl.register(collector, tb)
    assert 'tests.lantz.FalseDriver_duplicate1' in tb


def test_register_driver_decl_cls1(collector, driver_decl):
    """Test handling driver class issues : failed import no such module.

    """
    tb = {}
    d = list(driver_decl.traverse())[-1]
    d.driver = 'ecpy.tasks.foo:Task'
    driver_decl.register(collector, tb)
    assert 'ecpy.lantz.Task' in tb and 'import' in tb['ecpy.lantz.Task']


def test_register_driver_decl_drivercls1_bis(collector, driver_decl):
    """Test handling driver class issues : failed import error while importing.

    """
    tb = {}
    d = list(driver_decl.traverse())[-1]
    d.driver = 'ecpy.testing.broken_module:Task'
    driver_decl.register(collector, tb)
    assert 'ecpy.lantz.Task' in tb and 'NameError' in tb['ecpy.lantz.Task']


def test_register_driver_decl_drivercls2(collector, driver_decl):
    """Test handling driver class issues : undefined in module.

    """
    tb = {}
    d = list(driver_decl.traverse())[-1]
    d.driver = 'ecpy.tasks.base_tasks:Task'
    driver_decl.register(collector, tb)
    assert 'ecpy.lantz.Task' in tb and 'attribute' in tb['ecpy.lantz.Task']


def test_register_driver_decl_drivercls3(collector, driver_decl):
    """Test handling driver class issues : wrong type.

    """
    tb = {}
    d = list(driver_decl.traverse())[-1]
    d.driver = 'tests.instruments.test_driver_decl:DEFAULT_MEMBERS'
    driver_decl.register(collector, tb)
    assert ('tests.lantz.DEFAULT_MEMBERS' in tb and
            'callable' in tb['tests.lantz.DEFAULT_MEMBERS'])


def test_unregister_driver_decl1(collector, driver_decl):
    """Test unregistering a driver.

    """
    driver_decl.register(collector, {})
    driver_decl.unregister(collector)
    assert not collector.contributions


def test_unregister_driver_decl2(collector, driver_decl):
    """Test unregistering a driver which already disappeared.

    """
    driver_decl.register(collector, {})
    collector.contributions = {}
    driver_decl.unregister(collector)
    # Would raise an error if the error was not properly catched.


def test_str_driver(driver_decl):
    """Test string representation.

    """
    str(driver_decl)
