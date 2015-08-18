# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test dependency collection functions.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from operator import getitem
from collections import defaultdict

from future.builtins import str

from ecpy.tasks.manager.utils.dependencies import (collect_task,
                                                   collect_interface)


def test_collect_task_dependencies(task_workbench):
    """Test collecting the dependencies found in a task.

    """
    runtime = ['test']
    plugin = task_workbench.get_plugin('ecpy.tasks')
    plugin.get_task_infos('ComplexTask').dependencies = runtime

    dep = dict()
    errors = dict()
    run = collect_task(task_workbench, {'task_class': 'ComplexTask'}, getitem,
                       dep, errors)

    assert run == runtime
    assert 'ComplexTask' in dep
    assert not errors

    dep.clear()
    run = collect_task(task_workbench, {'task_class': '__dummy__'}, getitem,
                       dep, errors)
    assert not run
    assert not dep
    assert '__dummy__' in errors


def test_collect_interface_dependencies(task_workbench):
    """Test collecting the dependencies found in an interface.

    """
    runtime = ['test']
    interface = ('LinspaceLoopInterface', 'LoopTask')
    plugin = task_workbench.get_plugin('ecpy.tasks')
    plugin.get_interface_infos(interface).dependencies = runtime

    dep = defaultdict(dict)
    errors = defaultdict(dict)
    run = collect_interface(task_workbench,
                            {'interface_class': str(interface)},
                            getitem, dep, errors)

    assert run == runtime
    assert interface in dep
    assert not errors

    dep.clear()
    run = collect_interface(task_workbench,
                            {'interface_class': ('__dummy__', 'LoopTask')},
                            getitem, dep, errors)
    assert not run
    assert not dep
    assert str(('__dummy__', 'LoopTask')) in errors
