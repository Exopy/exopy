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
from configobj import ConfigObj

from ecpy.instruments.user import InstrUser
from ecpy.instruments.plugin import validate_user
from ecpy.instruments.infos import DriverInfos
from ecpy.testing.util import handle_dialog, process_app_events

from .conftest import PROFILE_PATH
with enaml.imports():
    from .contributors import (InstrContributor1, InstrContributor2,
                               InstrContributor3)


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

    assert 'tests_' in p.users
    assert 'false_starter_bis' in p.starters
    assert 'false_connection_bis' in p.connections
    assert 'false_settings_bis' in p.settings

    # Test observation of profiles folders
    shutil.copy(PROFILE_PATH, p._profiles_folders[0])
    sleep(0.1)
    process_app_events()

    assert 'fp' in p.profiles

    os.remove(os.path.join(p._profiles_folders[0], 'fp.instr.ini'))
    sleep(0.1)
    process_app_events()

    assert 'fp' not in p.profiles

    # Test dynamic unregsitrations (same remark as above)
    instr_workbench.unregister(c2.id)

    assert 'tests_' not in p.users
    assert 'false_starter_bis' not in p.starters
    assert 'false_connection_bis' not in p.connections
    assert 'false_settings_bis' not in p.settings

    assert 'Dummy' in p._manufacturers._manufacturers  # dummy is an alias

    # Stop
    p.stop()


def test_handling_crash_of_watchdog(instr_workbench, caplog):
    """Test handling that we can close even if the observer fail to join.

    """
    instr_workbench.register(InstrContributor1())

    # Test starting
    p = instr_workbench.get_plugin('ecpy.instruments')

    o = p._observer
    j = o.join

    def false_join():
        import logging
        logging.critical('Crash')
        raise RuntimeError()

    o.join = false_join

    p.stop()
    j()
    assert any(r.levelname == 'CRITICAL' for r in caplog.records())


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


def test_handle_corrupted_profile(prof_plugin, caplog):
    """Test that if a profile is not validated a proper warning is emitted

    """
    c = ConfigObj(os.path.join(prof_plugin._profiles_folders[0],
                               'fp1.instr.ini'))
    del c['id']
    c.write()

    prof_plugin._refresh_profiles()

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
    process_app_events()

    assert 'fp' in p.profiles

    os.remove(os.path.join(p._profiles_folders[0], 'fp.instr.ini'))
    sleep(0.5)
    process_app_events()

    assert 'fp' not in p.profiles


def test_create_connection(instr_workbench):
    """Test creating a connection.

    """
    instr_workbench.register(InstrContributor1())
    p = instr_workbench.get_plugin('ecpy.instruments')

    d = dict((i, i**2) for i in range(10))
    c = p.create_connection('false_connection', d)
    assert c.defaults == d


def test_create_settings(instr_workbench):
    """Test creating a settings.

    """
    instr_workbench.register(InstrContributor1())
    p = instr_workbench.get_plugin('ecpy.instruments')

    d = dict((i, i**2) for i in range(10))
    c = p.create_settings('false_settings', d)
    assert c.defaults == d


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


def test_get_profiles(prof_plugin):
    """Test requesting profiles from the plugin.

    """
    p, m = prof_plugin.get_profiles('tests2', ['fp1', 'fp2'])
    assert not m and 'fp1' in p and 'fp2' in p
    assert prof_plugin.used_profiles == {'fp1': 'tests2', 'fp2': 'tests2'}


def test_get_aliases(prof_plugin):
    """Test requesting a manufacturer aliases.

    """
    a = prof_plugin.get_aliases('Dummy')
    assert len(a) == 1


def test_requesting_driver_already_owned_and_accept_partial(prof_plugin):
    """Test requesting profiles owned by other users.

    """
    prof_plugin.used_profiles = {'fp1': 'tests3', 'fp2': 'tests3',
                                 'fp3': 'tests2'}
    p, m = prof_plugin.get_profiles('tests', ['fp1', 'fp2', 'fp3'],
                                    try_release=True, partial=True)
    assert 'fp1' in p
    assert 'fp2' in m and 'fp3' in m


def test_requesting_driver_already_owned_and_reject_partial(prof_plugin):
    """Test requesting profiles owned by other users.

    """
    prof_plugin.used_profiles = {'fp1': 'tests3', 'fp2': 'tests3',
                                 'fp3': 'tests2'}
    p, m = prof_plugin.get_profiles('tests', ['fp1', 'fp2', 'fp3'],
                                    try_release=True, partial=False)
    assert not p
    assert 'fp2' in m and 'fp3' in m
    assert 'fp1' not in prof_plugin.used_profiles


def test_get_profiles_no_partial_no_release(prof_plugin):
    """Test requesting used profiles with no_partial and no_release.

    """
    prof_plugin.used_profiles = {'fp1': 'tests'}
    p, m = prof_plugin.get_profiles('tests2', ['fp1', 'fp2'],
                                    try_release=False, partial=False)
    assert not p
    assert 'fp1' in m and 'fp2' not in m


def test_get_profiles_for_unknown_user(prof_plugin):
    """Test requesting profiles from the plugin.

    """
    with pytest.raises(ValueError):
        prof_plugin.get_profiles('unknown', ['fp1'])


def test_release_profiles(prof_plugin):
    """Test releasing a previously acquired profile.

    """
    prof_plugin.used_profiles = {'fp1': 'tests3', 'fp2': 'tests3',
                                 'fp3': 'tests2'}
    prof_plugin.release_profiles('tests3', ['fp1', 'fp2', 'fp3'])
    assert 'fp1' not in prof_plugin.used_profiles
    assert 'fp2' not in prof_plugin.used_profiles
    assert 'fp3' in prof_plugin.used_profiles


def test_driver_validation_error_handler(windows, instr_workbench):
    """Test the error handler dedicated to driver validation issues.

    """
    core = instr_workbench.get_plugin('enaml.workbench.core')
    p = instr_workbench.get_plugin('ecpy.instruments')
    d = DriverInfos(starter='starter', connections={'c1': {}, 'c2': {}},
                    settings={'s2': {}, 's3': {}})
    cmd = 'ecpy.app.errors.signal'

    def check_dialog(dial):
        w = dial.errors['ecpy.driver-validation']
        assert 'd' in w.errors
        for err in ('starter', 'connections', 'settings'):
            assert err in w.errors[d]

    with handle_dialog('accept', check_dialog):
        core.invoke_command(cmd, {'kind': 'ecpy.driver-validation',
                                  'details': {'d': d.validate(p)}})


def test_validate_runtime_dependencies_driver(instr_workbench):
    """Test the validation of drivers as runtime dependencies.

    """
    instr_workbench.register(InstrContributor1())

    d_p = instr_workbench.get_plugin('ecpy.app.dependencies')
    d_c = d_p.run_deps_collectors.contributions['ecpy.instruments.drivers']

    err = {}
    d_c.validate(instr_workbench, ('tests.test.FalseDriver', 'dummy'), err)

    assert len(err) == 1
    assert 'tests.test.FalseDriver' not in err['unknown-drivers']
    assert 'dummy' in err['unknown-drivers']


def test_collect_runtime_dependencies_driver(instr_workbench):
    """Test the collection of drivers as runtime dependencies.

    """
    instr_workbench.register(InstrContributor1())

    d_p = instr_workbench.get_plugin('ecpy.app.dependencies')
    d_c = d_p.run_deps_collectors.contributions['ecpy.instruments.drivers']

    dep = dict.fromkeys(('tests.test.FalseDriver', 'dummy'))
    err = {}
    un = set()
    d_c.collect(instr_workbench, 'tests', dep, un, err)

    assert len(err) == 1
    assert 'tests.test.FalseDriver' not in err['unknown-drivers']
    assert 'dummy' in err['unknown-drivers']

    assert not un

    assert dep['tests.test.FalseDriver'] is not None
    assert dep['dummy'] is None


def test_validate_runtime_dependencies_profiles(prof_plugin):
    """Test the validation of profiles as runtime dependencies.

    """
    w = prof_plugin.workbench

    d_p = w.get_plugin('ecpy.app.dependencies')
    d_c = d_p.run_deps_collectors.contributions['ecpy.instruments.profiles']

    err = {}
    d_c.validate(w, ('fp1', 'dummy'), err)

    assert len(err) == 1
    assert 'fp1' not in err['unknown-profiles']
    assert 'dummy' in err['unknown-profiles']


def test_collect_release_runtime_dependencies_profiles(prof_plugin):
    """Test the collection and release of profiles as runtime dependencies.

    """
    w = prof_plugin.workbench

    d_p = w.get_plugin('ecpy.app.dependencies')
    d_c = d_p.run_deps_collectors.contributions['ecpy.instruments.profiles']

    dep = dict.fromkeys(('fp1', 'dummy'))
    err = {}
    un = set()
    d_c.collect(w, 'tests', dep, un, err)

    assert len(err) == 1
    assert 'dummy' in err['unknown-profiles']

    assert not un

    assert dep['fp1'] is not None
    assert dep['dummy'] is None

    assert 'fp1' in prof_plugin.used_profiles

    d_c.release(w, 'tests', list(dep))

    assert not prof_plugin.used_profiles

    prof_plugin.used_profiles = {'fp2': 'tests2'}
    dep = dict.fromkeys(('fp1', 'fp2', 'dummy'))
    err = {}
    un = set()
    d_c.collect(w, 'tests', dep, un, err)

    assert len(err) == 1
    assert 'dummy' in err['unknown-profiles']

    assert 'fp2' in un

    assert dep['fp1'] is None
    assert dep['fp2'] is None
    assert dep['dummy'] is None
