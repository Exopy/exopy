# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the measurement object capabilities.

"""
import os

import pytest
import enaml

from exopy.measurement.measurement import Measurement
from exopy.tasks.api import RootTask

with enaml.imports():
    from exopy.tasks.manifest import TasksManagerManifest
    from exopy.testing.measurement.contributions import Flags


@pytest.mark.parametrize('kind', ['pre-hook', 'monitor', 'post-hook'])
def test_tool_handling(measurement, kind):
    """Test adding/moving and removing a tool from a measurement.

    """
    def member():
        return getattr(measurement, kind.replace('-', '_')+'s')

    measurement.add_tool(kind, 'dummy')

    assert 'dummy' in member()
    assert member()['dummy'].measurement is measurement

    with pytest.raises(KeyError):
        measurement.add_tool(kind, 'dummy')

    if kind == 'pre-hook':
        assert list(member())[1] == 'dummy'
        measurement.move_tool(kind, 1, 0)
        assert list(member())[0] == 'dummy'

    measurement.remove_tool(kind, 'dummy')
    assert 'dummy' not in member()

    with pytest.raises(KeyError):
        measurement.remove_tool(kind, 'dummy')


def test_tool_function_kind_checking(measurement):
    """Simply check that kind checking is correctly enforced in all tool
    handling functions.

    """
    for f in ('add_tool', 'remove_tool', 'move_tool'):
        with pytest.raises(ValueError):
            m = getattr(measurement, f)
            if f == 'move_tool':
                m('', 0, 1)
            else:
                m('', None)

    with pytest.raises(ValueError):
        measurement.move_tool('monitor', 0, 1)


def test_measurement_persistence(measurement_workbench, measurement, tmpdir,
                                 monkeypatch):
    """Test saving and reloading a measurement.

    """
    measurement_workbench.register(TasksManagerManifest())
    plugin = measurement_workbench.get_plugin('exopy.measurement')

    for m_e in ('meas_name', 'meas_id', 'meas_date', 'meas_time'):
        assert m_e in measurement.root_task.database_entries
    measurement.add_tool('pre-hook', 'dummy')
    measurement.root_task.default_path = 'test'
    measurement.pre_hooks['dummy'].fail_check = True

    path = str(tmpdir.join('test.meas.ini'))
    measurement.save(path)
    assert measurement.path == path

    loaded, errors = Measurement.load(plugin, path)
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

    loaded, errors = Measurement.load(plugin, path)
    assert loaded is None
    assert 'main task' in errors and 'CommandError' in errors['main task']

    CorePlugin.invoke_command = old

    class CreationError(Exception):
        pass

    class Fail(object):
        def new(self, workbench, default=True):
            raise CreationError()

    plugin._pre_hooks.contributions['dummy'] = Fail()

    loaded, errors = Measurement.load(plugin, path)
    assert loaded is None
    assert 'pre-hook' in errors and 'dummy' in errors['pre-hook']
    assert 'CreationError' in errors['pre-hook']['dummy']


def test_running_checks(measurement_workbench, measurement):
    """Test running the checks attached to a measurement.

    """
    # Add dummy hooks
    measurement.add_tool('pre-hook', 'dummy')
    measurement.add_tool('post-hook', 'dummy')

    # This is necessary for the internal checks.
    measurement_workbench.register(TasksManagerManifest())

    # Collect run time dependencies.
    res, msg, errors = measurement.dependencies.collect_runtimes()
    assert res

    # Fake the presence of run time dependencies to check that they are well
    # passed to the root task.
    measurement.dependencies._runtime_map['main'] = {'dummy': (1, 2, 3)}
    measurement.dependencies._runtime_dependencies['dummy'] =\
        {1: None, 2: None, 3: None}

    # Check that the internal hook does run the root_task tests.
    res, errors = measurement.run_checks()
    assert not res
    assert 'exopy.internal_checks' in errors

    # Check an ideal case
    measurement.root_task.default_path = os.path.dirname(__file__)
    res, errors = measurement.run_checks()
    assert res
    assert not errors

    # Check handling error in pre_hook
    measurement.pre_hooks['dummy'].fail_check = True
    res, errors = measurement.run_checks()
    assert not res
    assert 'dummy' in errors and errors['dummy'] == 'pre'

    # Check handling error in post_hook
    measurement.pre_hooks['dummy'].fail_check = False
    measurement.post_hooks['dummy'].fail_check = True
    res, errors = measurement.run_checks()
    assert not res
    assert 'dummy' in errors and errors['dummy'] == 'post'

    # Check kwargs passing to pre-hooks
    measurement.post_hooks['dummy'].fail_check = False
    res, errors = measurement.run_checks(fail=True)
    assert not res
    assert 'dummy' in errors and errors['dummy'] == 'pre'

    # Check kwargs passing to post-hooks
    res, errors = measurement.run_checks(fail_post=True)
    assert not res
    assert 'dummy' in errors and errors['dummy'] == 'post'


def test_changing_state(measurement):
    """Test going from edition to running and back.

    """
    measurement.add_tool('monitor', 'dummy')

    def add_entry(measurement, name, value):
        entries = measurement.root_task.database_entries.copy()
        entries[name] = value
        measurement.root_task.database_entries = entries

    add_entry(measurement, 'test', 1)
    assert 'root/test' in measurement.monitors['dummy'].monitored_entries

    measurement.enter_running_state()
    add_entry(measurement, 'test2', 2)
    assert 'root/test2' not in measurement.monitors['dummy'].monitored_entries

    measurement.enter_edition_state()
    add_entry(measurement, 'test3', 2)
    assert 'root/test3' in measurement.monitors['dummy'].monitored_entries

    entries = measurement.collect_monitored_entries()
    assert 'root/test' in entries and 'root/test3' in entries
    assert 'root/test2' not in entries


# =============================================================================
# --- Test dependencies handling ----------------------------------------------
# =============================================================================

def test_accessing_build_dependencies(measurement, monkeypatch):
    """Test accessing and collecting if necessary build dependencies.

    """
    class RT(RootTask):

        dep_type = 'unknown'

    # Fail analysis because
    measurement.root_task = RT()
    deps = measurement.dependencies.get_build_dependencies()
    assert 'unknown' in deps.errors

    class RT(RootTask):

        dep_type = 'dummy'

    # Fail collection
    measurement.root_task = RT()
    monkeypatch.setattr(Flags, 'BUILD_FAIL_COLLECT', True)
    deps = measurement.dependencies.get_build_dependencies()
    assert 'dummy' in deps.errors

    # Succeed with cached analysis
    monkeypatch.setattr(Flags, 'BUILD_FAIL_ANALYSE', True)
    monkeypatch.setattr(Flags, 'BUILD_FAIL_COLLECT', False)
    deps = measurement.dependencies.get_build_dependencies()
    assert not deps.errors

    # Succeed with cached dependencies
    monkeypatch.setattr(Flags, 'BUILD_FAIL_COLLECT', True)
    deps = measurement.dependencies.get_build_dependencies()
    assert not deps.errors

    # Test reset for build related cache
    measurement.dependencies.reset()
    monkeypatch.setattr(Flags, 'BUILD_FAIL_COLLECT', False)
    monkeypatch.setattr(Flags, 'BUILD_FAIL_ANALYSE', True)
    deps = measurement.dependencies.get_build_dependencies()
    assert 'dummy' in deps.errors


def test_collecting_runtime(measurement, monkeypatch):
    """Test collecting/releasing runtimes.

    """
    measurement.add_tool('pre-hook', 'dummy')
    measurement.add_tool('post-hook', 'dummy')

    class RT(RootTask):

        dep_type = 'dummy'

    measurement.root_task = RT()

    root = measurement.root_task

    # Fail analysing main task build
    monkeypatch.setattr(Flags, 'BUILD_FAIL_ANALYSE', True)
    res, msg, errors = measurement.dependencies.collect_runtimes()
    assert not res
    assert 'main' in msg and 'build' in msg

    res, msg, errors = measurement.dependencies.collect_task_runtimes(root)
    assert not res
    assert 'main' in msg and 'build' in msg


    # Fail analysing main task runtime
    monkeypatch.setattr(Flags, 'BUILD_FAIL_ANALYSE', False)
    monkeypatch.setattr(Flags, 'RUNTIME1_FAIL_ANALYSE', True)
    res, msg, errors = measurement.dependencies.collect_runtimes()
    assert not res
    assert 'main' in msg and 'runtime' in msg

    res, msg, errors = measurement.dependencies.collect_task_runtimes(root)
    assert not res
    assert 'main' in msg and 'runtime' in msg


    # Fail analysing hook runtime
    monkeypatch.setattr(Flags, 'RUNTIME1_FAIL_ANALYSE', False)
    monkeypatch.setattr(Flags, 'RUNTIME2_FAIL_ANALYSE', True)
    res, msg, errors = measurement.dependencies.collect_runtimes()
    assert not res
    assert 'hook' in msg and 'runtime' in msg



    # Fail collecting main task runtimes
    monkeypatch.setattr(Flags, 'RUNTIME2_FAIL_ANALYSE', False)
    monkeypatch.setattr(Flags, 'RUNTIME1_FAIL_COLLECT', True)
    res, msg, errors = measurement.dependencies.collect_runtimes()
    assert not res
    assert 'collect' in msg and 'runtime' in msg

    res, msg, errors = measurement.dependencies.collect_task_runtimes(root)
    assert not res
    assert 'collect' in msg and 'runtime' in msg


    # Fail collecting hook runtimes
    monkeypatch.setattr(Flags, 'RUNTIME1_FAIL_COLLECT', False)
    monkeypatch.setattr(Flags, 'RUNTIME2_FAIL_COLLECT', True)
    res, msg, errors = measurement.dependencies.collect_runtimes()
    assert not res
    assert 'collect' in msg and 'runtime' in msg


    # Runtimes unavailable
    monkeypatch.setattr(Flags, 'RUNTIME2_FAIL_COLLECT', False)
    monkeypatch.setattr(Flags, 'RUNTIME1_UNAVAILABLE', True)
    res, msg, errors = measurement.dependencies.collect_runtimes()
    assert not res
    assert 'unavailable' in msg
    deps = measurement.dependencies
    assert 'dummy1' in deps.get_runtime_dependencies('main')
    assert deps.get_runtime_dependencies('main')['dummy1'] == {}
    measurement.dependencies.release_runtimes()

    res, msg, errors = measurement.dependencies.collect_task_runtimes(root)
    assert not res
    assert 'unavailable' in msg
    deps = measurement.dependencies
    assert 'dummy1' in deps.get_runtime_dependencies('main')
    assert deps.get_runtime_dependencies('main')['dummy1'] == {}
    measurement.dependencies.release_runtimes()


    # Runtimes unavailable for hooks
    monkeypatch.setattr(Flags, 'RUNTIME1_UNAVAILABLE', False)
    monkeypatch.setattr(Flags, 'RUNTIME2_UNAVAILABLE', True)
    res, msg, errors = measurement.dependencies.collect_runtimes()
    assert not res
    assert 'unavailable' in msg
    measurement.dependencies.release_runtimes()


    # Succeed collecting.
    monkeypatch.setattr(Flags, 'RUNTIME2_UNAVAILABLE', False)
    res, msg, errors = measurement.dependencies.collect_runtimes()
    assert res
    res, msg, errors = measurement.dependencies.collect_task_runtimes(root)
    assert res

    # Collecting when already collected
    monkeypatch.setattr(Flags, 'RUNTIME1_UNAVAILABLE', True)
    res, msg, errors = measurement.dependencies.collect_runtimes()
    assert res
    res, msg, errors = measurement.dependencies.collect_task_runtimes(root)
    assert res

    # Access for unknown id
    assert not measurement.dependencies.get_runtime_dependencies('unknown')

    # Access for known id
    assert measurement.dependencies.get_runtime_dependencies('dummy')

    # Release and test impossibility to access for uncollected deps.
    measurement.dependencies.release_runtimes()
    with pytest.raises(RuntimeError):
        measurement.dependencies.get_runtime_dependencies('dummy')

    # Test reseting
    measurement.dependencies.reset()
    res, msg, errors = measurement.dependencies.collect_runtimes()
    assert not res

    # Test reseting while holding dependencies.
    monkeypatch.setattr(Flags, 'RUNTIME1_UNAVAILABLE', False)
    res, msg, errors = measurement.dependencies.collect_runtimes()
    with pytest.raises(RuntimeError):
        measurement.dependencies.reset()
    measurement.dependencies.release_runtimes()
    # Check that this does not crash
    measurement.dependencies.release_runtimes()
