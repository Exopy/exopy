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
    from ecpy.tasks.manager.manifest import TasksManagerManifest
    from .contributions import MeasureTestManifest


@pytest.fixture
def measure(measure_workbench):
    """Register the dummy testing tools and create an empty measure.

    """
    measure_workbench.register(MeasureTestManifest())
    plugin = measure_workbench.get_plugin('ecpy.measure')
    measure = Measure(plugin=plugin, root_task=RootTask(),
                      name='Dummy', id='001')
    return measure


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
        assert member().keys()[1] == 'dummy'
        measure.move_tool(kind, 1, 0)
        assert member().keys()[0] == 'dummy'

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

    measure.add_tool('pre-hook', 'dummy')
    measure.root_task.default_path = 'test'
    measure.pre_hooks['dummy'].fail_check = True

    path = str(tmpdir.join('test.meas.ini'))
    measure.save(path)
    assert measure.path == path

    loaded, errors = Measure.load(plugin, path)
    print(errors)
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
    monkeypatch.setattr(CorePlugin, 'invoke_command', generate_err)

    class CreationError(Exception):
        pass

    class Fail(object):
        def new(self, workbench, default=True):
            raise CreationError()

    plugin._pre_hooks.contributions['dummy'] = Fail()

    loaded, errors = Measure.load(plugin, path)
    assert loaded is None
    assert 'main task' in errors and 'CommandError' in errors['main task']
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
    res, msg, errors = measure.dependencies.collect_runtimes()
    assert res

    # Check that the internal hook does run the root_task tests.
    res, errors = measure.run_checks()
    assert not res
    assert 'Internal checks' in errors

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

    assert sorted(measure.collect_monitored_entries()) ==\
        sorted(['root/test', 'root/test3'])


def test_dependencies(measure):
    """
    """
    pass
