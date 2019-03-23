# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test DependenciesManagerPLugin behavior.

"""
import pytest
import enaml
from configobj import ConfigObj

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from exopy.app.dependencies.manifest import DependenciesManifest

    from .dependencies_utils import (BuildDep, RuntimeDep)


ANALYSE = 'exopy.app.dependencies.analyse'

VALIDATE = 'exopy.app.dependencies.validate'

COLLECT = 'exopy.app.dependencies.collect'

RELEASE = 'exopy.app.dependencies.release_runtimes'


# =============================================================================
# --- Fixtures ----------------------------------------------------------------
# =============================================================================

@pytest.yield_fixture
def dep_workbench(workbench):
    """Setup the workbench to test dependencies related capabilities.

    """
    workbench.register(CoreManifest())
    workbench.register(DependenciesManifest())
    workbench.register(BuildDep())
    workbench.register(RuntimeDep())

    yield workbench

    workbench.unregister('exopy.app.dependencies')
    workbench.unregister('enaml.workbench.core')


@pytest.fixture
def dependent_object():
    """Access an instance of an object having dependencies.

    """

    class Obj(object):

        dep_type = 'test'

        val = 'r'

        run = 2

        def traverse(self):
            yield self

        def __str__(self):
            return 'Test_object'

    return Obj()


@pytest.fixture
def build_deps(dep_workbench, dependent_object):
    """Get the build dependencies of a dependent_object.

    """
    core = dep_workbench.get_plugin('enaml.workbench.core')
    dep = core.invoke_command(ANALYSE, {'obj': dependent_object})
    return dep.dependencies


@pytest.fixture
def runtime_deps(dep_workbench, dependent_object):
    """Get the runtime dependencies of a dependent_object.

    """
    core = dep_workbench.get_plugin('enaml.workbench.core')
    dep = core.invoke_command(ANALYSE, {'obj': dependent_object,
                                        'dependencies': ['runtime']}
                              )
    return dep.dependencies


# =============================================================================
# --- Analysing ---------------------------------------------------------------
# =============================================================================

def test_analysing_build(dep_workbench, dependent_object):
    """Test analysing only the build dependencies.

    """
    core = dep_workbench.get_plugin('enaml.workbench.core')
    dep = core.invoke_command(ANALYSE, {'obj': dependent_object})
    assert not dep.errors
    assert 'test' in dep.dependencies
    assert 'r' in dep.dependencies['test']


def test_analysing_build_from_config(dep_workbench):
    """Test analysing the build dependencies based on a ConfigObj.

    """
    core = dep_workbench.get_plugin('enaml.workbench.core')
    # nested field ensures that we skip object missing a dep_type
    dep = core.invoke_command(ANALYSE,
                              {'obj': ConfigObj({'val': '1',
                                                 'dep_type': 'test',
                                                 'nested': {}})}
                              )
    assert not dep.errors
    assert 'test' in dep.dependencies
    assert '1' in dep.dependencies['test']


def test_analysing_runtime(dep_workbench, dependent_object):
    """Test analysing only the runtime dependencies.

    """
    core = dep_workbench.get_plugin('enaml.workbench.core')
    dep = core.invoke_command(ANALYSE, {'obj': dependent_object,
                                        'dependencies': ['runtime']}
                              )
    assert not dep.errors
    assert 'test_run_collect' in dep.dependencies
    assert 2 in dep.dependencies['test_run_collect']


def test_analysing_all(dep_workbench, dependent_object):
    """Test analysing all dependencies.

    """
    core = dep_workbench.get_plugin('enaml.workbench.core')
    b_dep, r_dep = core.invoke_command(ANALYSE,
                                       {'obj': dependent_object,
                                        'dependencies': ['build',
                                                         'runtime']})

    assert not b_dep.errors and not r_dep.errors
    assert 'test' in b_dep.dependencies
    assert 'test_run_collect' in r_dep.dependencies


def test_handling_analysing_errors(dep_workbench, dependent_object):
    """Test handling errors occuring when analysing dependencies.

    """
    plugin = dep_workbench.get_plugin('exopy.app.dependencies')

    for b in plugin.build_deps.contributions.values():
        setattr(b, 'err', True)

    for r in plugin.run_deps_analysers.contributions.values():
        setattr(r, 'err', True)

    core = dep_workbench.get_plugin('enaml.workbench.core')
    b_dep, r_dep = core.invoke_command(ANALYSE,
                                       {'obj': dependent_object,
                                        'dependencies': ['build',
                                                         'runtime']})

    assert 'test' in b_dep.errors and 'test_run_collect' in r_dep.errors
    assert b_dep.errors['test'].get('Test_object')
    assert r_dep.errors['test_run_collect'].get('Test_object')


def test_handling_analysing_exception_in_build(dep_workbench,
                                               dependent_object):
    """Test handling errors occuring when analysing dependencies.

    """
    plugin = dep_workbench.get_plugin('exopy.app.dependencies')

    for b in plugin.build_deps.contributions.values():
        setattr(b, 'exc', True)

    core = dep_workbench.get_plugin('enaml.workbench.core')
    b_dep, r_dep = core.invoke_command(ANALYSE,
                                       {'obj': dependent_object,
                                        'dependencies': ['build',
                                                         'runtime']})

    assert 'test' in b_dep.errors
    assert 'unhandled' in b_dep.errors['test']


def test_handling_analysing_exception_in_runtime(dep_workbench,
                                                 dependent_object):
    """Test handling errors occuring when analysing dependencies.

    """
    plugin = dep_workbench.get_plugin('exopy.app.dependencies')

    for r in plugin.run_deps_analysers.contributions.values():
        setattr(r, 'exc', True)

    core = dep_workbench.get_plugin('enaml.workbench.core')
    b_dep, r_dep = core.invoke_command(ANALYSE,
                                       {'obj': dependent_object,
                                        'dependencies': ['build',
                                                         'runtime']})

    assert 'test_run' in r_dep.errors
    assert 'unhandled' in r_dep.errors['test_run']


def test_handling_missing_build_analyser(dep_workbench, dependent_object):
    """Test analysing the dependencies of an object whose dep_type match
    no known collector.

    """
    dependent_object.dep_type = 'new'
    core = dep_workbench.get_plugin('enaml.workbench.core')
    dep = core.invoke_command(ANALYSE, {'obj': dependent_object})
    assert 'new' in dep.errors


def test_handling_missing_runtime_analyser(dep_workbench, dependent_object):
    """Test analysing the dependencies of an object for which a runtime
    collector is missing.

    """
    plugin = dep_workbench.get_plugin('exopy.app.dependencies')
    for b in plugin.build_deps.contributions.values():
        setattr(b, 'run', ['dummy'])

    core = dep_workbench.get_plugin('enaml.workbench.core')
    dep = core.invoke_command(ANALYSE, {'obj': dependent_object,
                                        'dependencies': ['runtime']})

    assert 'runtime' in dep.errors and 'dummy' in dep.errors['runtime']


def test_handling_runtime_analyser_not_matching_a_collector(dep_workbench,
                                                            dependent_object):
    """Test analysing the dependencies of an object for which a runtime
    collector is missing.

    """
    plugin = dep_workbench.get_plugin('exopy.app.dependencies')
    for b in plugin.build_deps.contributions.values():
        setattr(b, 'run', ['run_test2'])

    core = dep_workbench.get_plugin('enaml.workbench.core')
    dep = core.invoke_command(ANALYSE, {'obj': dependent_object,
                                        'dependencies': ['runtime']})

    assert 'runtime' in dep.errors and 'collector' in dep.errors['runtime']


# =============================================================================
# --- Validating --------------------------------------------------------------
# =============================================================================

def test_validating_build(dep_workbench, build_deps):
    """Test validating build dependencies.

    """
    core = dep_workbench.get_plugin('enaml.workbench.core')
    res, err = core.invoke_command(VALIDATE, {'kind': 'build',
                                              'dependencies': build_deps})

    assert res


def test_validating_runtime(dep_workbench, runtime_deps):
    """Test validating runtime dependencies.

    """
    core = dep_workbench.get_plugin('enaml.workbench.core')
    res, err = core.invoke_command(VALIDATE, {'kind': 'runtime',
                                              'dependencies': runtime_deps})

    assert res


def test_validating_with_wrong_kind(dep_workbench):
    """Test handling of incorrect kind argument.

    """
    core = dep_workbench.get_plugin('enaml.workbench.core')
    with pytest.raises(ValueError):
        res, err = core.invoke_command(VALIDATE, {'kind': 'test',
                                                  'dependencies': {}})


def test_handling_validating_errors(dep_workbench, build_deps):
    """Test reporting errors.

    """
    build_deps['test'].add('t')
    core = dep_workbench.get_plugin('enaml.workbench.core')
    res, err = core.invoke_command(VALIDATE, {'kind': 'build',
                                              'dependencies': build_deps})

    assert not res
    assert 't' in err['test']


def test_handling_validating_exceptions(dep_workbench, build_deps):
    """Test dealing with unhandled exceptions.

    """
    plugin = dep_workbench.get_plugin('exopy.app.dependencies')

    for b in plugin.build_deps.contributions.values():
        setattr(b, 'exc', True)

    core = dep_workbench.get_plugin('enaml.workbench.core')
    res, err = core.invoke_command(VALIDATE, {'kind': 'build',
                                              'dependencies': build_deps})

    assert not res


def test_handling_missing_validator(dep_workbench, build_deps):
    """Test handling a missing validator

    """
    build_deps['dummy'] = set()
    core = dep_workbench.get_plugin('enaml.workbench.core')
    res, err = core.invoke_command(VALIDATE, {'kind': 'build',
                                              'dependencies': build_deps})

    assert not res


# =============================================================================
# --- Collecting --------------------------------------------------------------
# =============================================================================

def test_collecting_build(dep_workbench, build_deps):
    """Test collecting build dependencies.

    """
    core = dep_workbench.get_plugin('enaml.workbench.core')
    dep = core.invoke_command(COLLECT, {'kind': 'build',
                                        'dependencies': build_deps})

    assert dep.dependencies['test']['r'] is object
    assert not dep.errors


def test_collecting_runtime(dep_workbench, runtime_deps):
    """Test collecting runtime dependencies.

    """
    plugin = dep_workbench.get_plugin('exopy.app.dependencies')
    core = dep_workbench.get_plugin('enaml.workbench.core')
    dep = core.invoke_command(COLLECT, {'kind': 'runtime',
                                        'dependencies': runtime_deps,
                                        'owner': plugin.manifest.id})

    assert dep.dependencies['test_run_collect']['run'] == 1
    assert not dep.errors


def test_collecting_unavailable_runtime(dep_workbench, runtime_deps):
    """Test collecting unavailable runtimes.

    """
    plugin = dep_workbench.get_plugin('exopy.app.dependencies')
    core = dep_workbench.get_plugin('enaml.workbench.core')

    for r in plugin.run_deps_collectors.contributions.values():
        setattr(r, 'una', True)

    dep = core.invoke_command(COLLECT, {'kind': 'runtime',
                                        'dependencies': runtime_deps,
                                        'owner': plugin.manifest.id},
                              )
    assert not dep.errors
    assert 'run_bis' in dep.dependencies['test_run_collect']
    assert 'run' not in dep.dependencies['test_run_collect']
    assert dep.unavailable['test_run_collect'] == {'run'}


def test_handling_collection_errors(dep_workbench, build_deps):
    """Test handling errors occuring when collecting dependencies.

    """
    build_deps['test'].add('t')
    core = dep_workbench.get_plugin('enaml.workbench.core')
    b_dep = core.invoke_command(COLLECT,
                                {'kind': 'build',
                                 'dependencies': build_deps,
                                 'owner': 'exopy.test'})

    assert 't' in b_dep.errors['test']


def test_handling_collection_exceptions_in_build(dep_workbench, build_deps):
    """Test handling errors occuring when collecting dependencies.

    """
    plugin = dep_workbench.get_plugin('exopy.app.dependencies')

    for b in plugin.build_deps.contributions.values():
        setattr(b, 'exc', True)

    core = dep_workbench.get_plugin('enaml.workbench.core')
    b_dep = core.invoke_command(COLLECT,
                                {'kind': 'build',
                                 'dependencies': build_deps,
                                 'owner': 'exopy.test'})

    assert 'test' in b_dep.errors


def test_handling_collection_exceptions_in_runtime(dep_workbench,
                                                   runtime_deps):
    """Test handling errors occuring when collecting dependencies.

    """
    plugin = dep_workbench.get_plugin('exopy.app.dependencies')

    for r in plugin.run_deps_collectors.contributions.values():
        setattr(r, 'exc', True)

    core = dep_workbench.get_plugin('enaml.workbench.core')
    r_dep = core.invoke_command(COLLECT,
                                {'kind': 'runtime',
                                 'dependencies': runtime_deps,
                                 'owner': 'exopy.test'})

    assert 'test_run_collect' in r_dep.errors


def test_handling_missing_caller(dep_workbench, runtime_deps):
    """Test handling a missing caller when runtime dependencies are
    requested.

    """
    core = dep_workbench.get_plugin('enaml.workbench.core')
    dep = core.invoke_command(COLLECT, {'kind': 'runtime',
                                        'dependencies': runtime_deps})
    assert 'owner' in dep.errors


def test_handling_missing_collector(dep_workbench, build_deps):
    """Test handling an unknown collector.

    """
    build_deps['dummy'] = set()
    core = dep_workbench.get_plugin('enaml.workbench.core')
    dep = core.invoke_command(COLLECT, {'kind': 'build',
                                        'dependencies': build_deps})
    assert 'dummy' in dep.errors


def test_collecting_with_wrong_kind(dep_workbench):
    """Test handling of incorrect kind argument.

    """
    core = dep_workbench.get_plugin('enaml.workbench.core')
    with pytest.raises(ValueError):
        res, err = core.invoke_command(COLLECT, {'kind': 'test',
                                                 'dependencies': {}})


# =============================================================================
# --- Releasing ---------------------------------------------------------------
# =============================================================================

def test_releasing_runtimes(dep_workbench, runtime_deps):
    """Test releasing runtime dependencies.

    """
    plugin = dep_workbench.get_plugin('exopy.app.dependencies')
    core = dep_workbench.get_plugin('enaml.workbench.core')
    dep = core.invoke_command(COLLECT, {'kind': 'runtime',
                                        'dependencies': runtime_deps,
                                        'owner': plugin.manifest.id},
                              )
    # Ensure that an unknown runtime won't crash
    dep.dependencies['rr'] = {}
    core.invoke_command(RELEASE,
                        {'dependencies': dep.dependencies,
                         'owner': plugin.manifest.id},
                        )

    assert 'run' not in dep.dependencies['test_run_collect']


# =============================================================================
# --- API ---------------------------------------------------------------
# =============================================================================

def test_importing_api():
    """Test importing the definitions found in the api.py file.

    """
    from exopy.app.dependencies import api
    assert api.__all__
