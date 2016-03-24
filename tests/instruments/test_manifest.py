# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tests for the instrument manager manifest.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import enaml

from ecpy.instruments.infos import DriverInfos
from ecpy.testing.util import handle_dialog

with enaml.imports():
    from .contributors import InstrContributor1


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


# XXX test the commands
