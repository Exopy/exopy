# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tests for the instrument manager plugin.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os
import shutil
from time import sleep

import enaml
import pytest

from ecpy.instruments.user import InstrUser
from ecpy.instruments.plugin import validate_user

with enaml.imports():
    from .contributors import (InstrContributor1, InstrContributor2,
                               InstrContributor3)


PROFILE_PATH = os.path.join(os.path.dirname(__file__),
                            'false_profile.instr.ini')


def test_validate_user():
    """Test the validate instrument user function.

    """
    u = InstrUser()

    res, msg = validate_user(u)
    assert not res and 'id' in msg

    u.id = 'test'
    res, msg = validate_user(u)
    assert not res and 'policy' in msg

    u.policy = 'unreleasable'
    res, msg = validate_user(u)
    assert res

    # Other positive cases are tested test_plugin_lifecycle


def test_plugin_lifecycle(instr_workbench):
    """Test the plugin lifecycle (initial registration and later on).

    """
    instr_workbench.register(InstrContributor1())

    # Test starting
    p = instr_workbench.get_plugin('ecpy.instruments')

    assert 'tests' in p.users
    assert 'false_starter' in p.starters
    assert 'false_connection' in p.connections
    assert 'false_settings' in p.settings
    assert 'tests.test.FalseDriver' in p._drivers.contributions
    for d in p._drivers.contributions.values():
        assert d.valid
    assert p.get_aliases('Dummy')

    # Test later registration (incomplete as dynamic loading of driver is not
    # fully implemented).
    c2 = InstrContributor2()
    instr_workbench.register(c2)

    assert 'tests2' in p.users
    assert 'false_starter2' in p.starters
    assert 'false_connection2' in p.connections
    assert 'false_settings2' in p.settings

    # Test observation of profiles folders
    shutil.copy(PROFILE_PATH, p._profiles_folders[0])
    sleep(0.5)

    assert 'false_profile' in p.profiles

    os.remove(os.path.join(p._profiles_folders[0], 'false_profile.instr.ini'))
    sleep(0.5)

    assert 'false_profile' not in p.profiles

    # Test dynamic unregsitrations (same remark as above)
    instr_workbench.unregister(c2.id)

    assert 'tests2' not in p.users
    assert 'false_starter2' not in p.starters
    assert 'false_connection2' not in p.connections
    assert 'false_settings2' not in p.settings

    assert 'Dummy' in p._manufacturers._manufacturers  # dummy is an alias

    # Stop
    p.stop()


def test_handling_crash_of_watchdog(instr_workbench):
    """
    """
    pass


def test_plugin_handling_driver_validation_issue(instr_workbench):
    """Test that a failure at validating an error does raise the appropriate
    warning.

    """
    instr_workbench.register(InstrContributor3())

    with pytest.raises(Exception) as execinfo:
        instr_workbench.get_plugin('ecpy.instruments')

    assert 'Unexpected exceptions occured' in str(execinfo.value)


def test_handle_wrong_profile_dir(instr_workbench, caplog):
    """Test that an incorrect path in _profiles_dirs does not crash anything.

    """
    p = instr_workbench.get_plugin('ecpy.instruments')

    p._profiles_folders = ['dummy']
    p._refresh_profiles()

    for records in caplog.records():
        assert records.levelname == 'WARNING'


def test_profiles_observation(instr_workbench):
    """Test observing the profiles in the profile folders.

    """
    instr_workbench.register(InstrContributor1())

    # Test starting
    p = instr_workbench.get_plugin('ecpy.instruments')

    # Test observation of profiles folders
    shutil.copy(PROFILE_PATH, p._profiles_folders[0])
    sleep(0.5)

    assert 'false_profile' in p.profiles

    os.remove(os.path.join(p._profiles_folders[0], 'false_profile.instr.ini'))
    sleep(0.5)

    assert 'false_profile' not in p.profiles


def test_create_connection(instr_workbench):
    """Test creating a connection.

    """
    instr_workbench.register(InstrContributor1())
    p = instr_workbench.get_plugin('ecpy.instruments')

    d = dict((i, i**2) for i in range(10))
    c = p.create_connection('false_connection', d)
    assert c['false_connection'] == d


def test_create_settings(instr_workbench):
    """Test creating a settings.

    """
    instr_workbench.register(InstrContributor1())
    p = instr_workbench.get_plugin('ecpy.instruments')

    d = dict((i, i**2) for i in range(10))
    c = p.create_settings('false_settings', d)
    assert c['false_settings'] == d


def test_get_drivers(instr_workbench):
    """Test accessing drivers and their associated starters.

    """
    instr_workbench.register(InstrContributor1())
    p = instr_workbench.get_plugin('ecpy.instruments')

    d, m = p.get_drivers(['tests.test.FalseDriver', 'dum'])

    assert m == ['dum']
    assert 'tests.test.FalseDriver' in d
    d, s = d['tests.test.FalseDriver']
    from .false_driver import FalseDriver
    assert d is FalseDriver and s.id == 'false_starter'


# Test release and partial returns
def test_get_profiles():
    """
    """
    pass


def test_release_profiles():
    """
    """
    pass


def test_get_aliases():
    """
    """
    pass


def test_driver_validation_dialog():
    """
    """
    pass


def test_runtime_dependencies_collection():
    """
    """
    pass
