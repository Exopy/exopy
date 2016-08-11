# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the measure object capabilities.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os

import pytest
import enaml
from future.builtins import str

from ecpy.measure.measure import Measure
from ecpy.tasks.api import RootTask

with enaml.imports():
    from ecpy.tasks.manifest import TasksManagerManifest
    from ecpy.testing.measure.contributions import Flags


@pytest.mark.parametrize('kind', ['pre-hook', 'monitor', 'post-hook'])
def test_tool_handling(measure, kind):
    """Test adding/moving and removing a tool from a measure.

    """
    def member():
        return getattr(measure, kind.replace('-', '_')+'s')

    measure.add_tool(kind, 'dummy')

    assert 'dummy' in member()
    assert member()['dummy'].measure is measure

    with pytest.raises(KeyError):
        measure.add_tool(kind, 'dummy')

    if kind == 'pre-hook':
        assert list(member())[1] == 'dummy'
        measure.move_tool(kind, 1, 0)
        assert list(member())[0] == 'dummy'

    measure.remove_tool(kind, 'dummy')
    assert 'dummy' not in member()

    with pytest.raises(KeyError):
        measure.remove_tool(kind, 'dummy')


def test_tool_function_kind_checking(measure):
    """Simply check that kind checking is correctly enforced in all tool
    handling functions.

    """
    for f in ('add_tool', 'remove_tool', 'move_tool'):
        with pytest.raises(ValueError):
            m = getattr(measure, f)
            if f == 'move_tool':
                m('', 0, 1)
            else:
                m('', None)

    with pytest.raises(ValueError):
        measure.move_tool('monitor', 0, 1)


def test_measure_persistence(measure_workbench, measure, tmpdir, monkeypatch):
    """Test saving and reloading a measure.

    """
    measure_workbench.register(TasksManagerManifest())
    plugin = measure_workbench.get_plugin('ecpy.measure')

    for m_e in ('meas_name', 'meas_id', 'meas_date'):
        assert m_e in measure.root_task.database_entries
    measure.add_tool('pre-hook', 'dummy')
    measure.root_task.default_path = 'test'
    measure.pre_hooks['dummy'].fail_check = True

    path = str(tmpdir.join('test.meas.ini'))
    measure.save(path)
    assert measure.path == path

    loaded, errors = Measure.load(plugin, path)
    assert loaded.root_task.default_path == 'test'
    assert loaded.pre_hooks['dummy'].fail_check
    assert loaded.path == path
    assert not errors

    # Test handling errors : root_task rebuilding and tool rebuilding.
    class CommandError(Exception):
        pass

    def generate_err(self, cmd, infos, u=None):
        raise CommandError()

    from enaml.workbench.core.core_plugin import CorePlugin
    old = CorePlugin.invoke_command
    monkeypatch.setattr(CorePlugin, 'invoke_command', generate_err)

    loaded, errors = Measure.load(plugin, path)
    assert loaded is None
    assert 'main task' in errors and 'CommandError' in errors['main task']

    CorePlugin.invoke_command = old

    class CreationError(Exception):
        pass

    class Fail(object):
        def new(self, workbench, default=True):
            raise CreationError()

    plugin._pre_hooks.contributions['dummy'] = Fail()

    loaded, errors = Measure.load(plugin, path)
    assert loaded is None
    assert 'pre-hook' in errors and 'dummy' in errors['pre-hook']
    assert 'CreationError' in errors['pre-hook']['dummy']


def test_running_checks(measure_workbench, measure):
    """Test running the checks attached to a measure.

    """
    # Add dummy hooks
    measure.add_tool('pre-hook', 'dummy')
    measure.add_tool('post-hook', 'dummy')

    # This is necessary for the internal checks.
    measure_workbench.register(TasksManagerManifest())

    # Collect run time dependencies.
    res, msg, errors = measure.dependencies.collect_runtimes()
    assert res

    # Fake the presence of run time dependencies to check that they are well
    # passed to the root task.
    measure.dependencies._runtime_map['main'] = {'dummy': (1, 2, 3)}
    measure.dependencies._runtime_dependencies['dummy'] = {1: None, 2: None,
                                                           3: None}

    # Check that the internal hook does run the root_task tests.
    res, errors = measure.run_checks()
    assert not res
    assert 'ecpy.internal_checks' in errors

    # Check an ideal case
    measure.root_task.default_path = os.path.dirname(__file__)
    res, errors = measure.run_checks()
    assert res
    assert not errors

    # Check handling error in pre_hook
    measure.pre_hooks['dummy'].fail_check = True
    res, errors = measure.run_checks()
    assert not res
    assert 'dummy' in errors and errors['dummy'] == 'pre'

    # Check handling error in post_hook
    measure.pre_hooks['dummy'].fail_check = False
    measure.post_hooks['dummy'].fail_check = True
    res, errors = measure.run_checks()
    assert not res
    assert 'dummy' in errors and errors['dummy'] == 'post'

    # Check kwargs passing to pre-hooks
    measure.post_hooks['dummy'].fail_check = False
    res, errors = measure.run_checks(fail=True)
    assert not res
    assert 'dummy' in errors and errors['dummy'] == 'pre'

    # Check kwargs passing to post-hooks
    res, errors = measure.run_checks(fail_post=True)
    assert not res
    assert 'dummy' in errors and errors['dummy'] == 'post'


def test_changing_state(measure):
    """Test going from edition to running and back.

    """
    measure.add_tool('monitor', 'dummy')

    def add_entry(measure, name, value):
        entries = measure.root_task.database_entries.copy()
        entries[name] = value
        measure.root_task.database_entries = entries

    add_entry(measure, 'test', 1)
    assert 'root/test' in measure.monitors['dummy'].monitored_entries

    measure.enter_running_state()
    add_entry(measure, 'test2', 2)
    assert 'root/test2' not in measure.monitors['dummy'].monitored_entries

    measure.enter_edition_state()
    add_entry(measure, 'test3', 2)
    assert 'root/test3' in measure.monitors['dummy'].monitored_entries

    entries = measure.collect_monitored_entries()
    assert 'root/test' in entries and 'root/test3' in entries
    assert 'root/test2' not in entries


# =============================================================================
# --- Test dependencies handling ----------------------------------------------
# =============================================================================

def test_accessing_build_dependencies(measure, monkeypatch):
    """Test accessing and collecting if necessary build dependencies.

    """
    class RT(RootTask):

        dep_type = 'unknown'

    # Fail analysis because
    measure.root_task = RT()
    deps = measure.dependencies.get_build_dependencies()
    assert 'unknown' in deps.errors

    class RT(RootTask):

        dep_type = 'dummy'

    # Fail collection
    measure.root_task = RT()
    monkeypatch.setattr(Flags, 'BUILD_FAIL_COLLECT', True)
    deps = measure.dependencies.get_build_dependencies()
    assert 'dummy' in deps.errors

    # Succeed with cached analysis
    monkeypatch.setattr(Flags, 'BUILD_FAIL_ANALYSE', True)
    monkeypatch.setattr(Flags, 'BUILD_FAIL_COLLECT', False)
    deps = measure.dependencies.get_build_dependencies()
    assert not deps.errors

    # Succeed with cached dependencies
    monkeypatch.setattr(Flags, 'BUILD_FAIL_COLLECT', True)
    deps = measure.dependencies.get_build_dependencies()
    assert not deps.errors

    # Test reset for build related cache
    measure.dependencies.reset()
    monkeypatch.setattr(Flags, 'BUILD_FAIL_COLLECT', False)
    monkeypatch.setattr(Flags, 'BUILD_FAIL_ANALYSE', True)
    deps = measure.dependencies.get_build_dependencies()
    assert 'dummy' in deps.errors


def test_collecting_runtime(measure, monkeypatch):
    """Test collecting/releasing runtimes.

    """
    measure.add_tool('pre-hook', 'dummy')
    measure.add_tool('post-hook', 'dummy')

    class RT(RootTask):

        dep_type = 'dummy'

    measure.root_task = RT()

    # Fail analysing main task build
    monkeypatch.setattr(Flags, 'BUILD_FAIL_ANALYSE', True)
    res, msg, errors = measure.dependencies.collect_runtimes()
    assert not res
    assert 'main' in msg and 'build' in msg

    # Fail analysing main task runtime
    monkeypatch.setattr(Flags, 'BUILD_FAIL_ANALYSE', False)
    monkeypatch.setattr(Flags, 'RUNTIME1_FAIL_ANALYSE', True)
    res, msg, errors = measure.dependencies.collect_runtimes()
    assert not res
    assert 'main' in msg and 'runtime' in msg

    # Fail analysing hook runtime
    monkeypatch.setattr(Flags, 'RUNTIME1_FAIL_ANALYSE', False)
    monkeypatch.setattr(Flags, 'RUNTIME2_FAIL_ANALYSE', True)
    res, msg, errors = measure.dependencies.collect_runtimes()
    assert not res
    assert 'hook' in msg and 'runtime' in msg

    # Fail collecting main task runtimes
    monkeypatch.setattr(Flags, 'RUNTIME2_FAIL_ANALYSE', False)
    monkeypatch.setattr(Flags, 'RUNTIME1_FAIL_COLLECT', True)
    res, msg, errors = measure.dependencies.collect_runtimes()
    assert not res
    assert 'collect' in msg and 'runtime' in msg

    # Fail collecting hook runtimes
    monkeypatch.setattr(Flags, 'RUNTIME1_FAIL_COLLECT', False)
    monkeypatch.setattr(Flags, 'RUNTIME2_FAIL_COLLECT', True)
    res, msg, errors = measure.dependencies.collect_runtimes()
    assert not res
    assert 'collect' in msg and 'runtime' in msg

    # Runtimes unavailable
    monkeypatch.setattr(Flags, 'RUNTIME2_FAIL_COLLECT', False)
    monkeypatch.setattr(Flags, 'RUNTIME1_UNAVAILABLE', True)
    res, msg, errors = measure.dependencies.collect_runtimes()
    assert not res
    assert 'unavailable' in msg
    measure.dependencies.release_runtimes()

    # Runtimes unavailable for hooks
    monkeypatch.setattr(Flags, 'RUNTIME1_UNAVAILABLE', False)
    monkeypatch.setattr(Flags, 'RUNTIME2_UNAVAILABLE', True)
    res, msg, errors = measure.dependencies.collect_runtimes()
    assert not res
    assert 'unavailable' in msg
    measure.dependencies.release_runtimes()

    # Succeed collecting.
    monkeypatch.setattr(Flags, 'RUNTIME2_UNAVAILABLE', False)
    res, msg, errors = measure.dependencies.collect_runtimes()
    assert res

    # Collecting when already collected
    monkeypatch.setattr(Flags, 'RUNTIME1_UNAVAILABLE', True)
    res, msg, errors = measure.dependencies.collect_runtimes()
    assert res

    # Access for unknown id
    assert not measure.dependencies.get_runtime_dependencies('unknown')

    # Access for known id
    assert measure.dependencies.get_runtime_dependencies('dummy')

    # Release and test impossibilty to access for uncollected deps.
    measure.dependencies.release_runtimes()
    with pytest.raises(RuntimeError):
        measure.dependencies.get_runtime_dependencies('dummy')

    # Test reseting
    measure.dependencies.reset()
    res, msg, errors = measure.dependencies.collect_runtimes()
    assert not res

    # Test reseting while holding dependencies.
    monkeypatch.setattr(Flags, 'RUNTIME1_UNAVAILABLE', False)
    res, msg, errors = measure.dependencies.collect_runtimes()
    with pytest.raises(RuntimeError):
        measure.dependencies.reset()
    measure.dependencies.release_runtimes()
    measure.dependencies.release_runtimes()  # Check that this does not crash
