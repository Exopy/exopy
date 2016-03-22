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

with enaml.imports():
    from .contributors import (InstrContributor1, InstrContributor2,
                               InstrContributor3)


PROFILE_PATH = os.path.join(os.path.dirname(__file__),
                            'false_profile.instr.ini')


def test_validate_user():
    """
    """
    pass


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

    # Stop
    p.stop()


def test_plugin_handling_driver_validation_issue(instr_workbench):
    """Test that a failure at validating an error does raise the appropriate
    warning.

    """
    instr_workbench.register(InstrContributor3())

    with pytest.raises(Exception) as execinfo:
        instr_workbench.get_plugin('ecpy.instruments')

    assert 'Unexpected exceptions occured' in str(execinfo.value)


def test_profiles_observation():
    """
    """
    pass


def test_get_connection():
    """
    """
    pass


def test_get_settings():
    """
    """
    pass


def test_get_drivers():
    """
    """
    pass


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
