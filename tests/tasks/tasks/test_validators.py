# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tests for the feval tagged members fields validators.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import numbers
from multiprocessing import Event

import pytest
from atom.api import Unicode

from ecpy.tasks.api import RootTask, validators
from ecpy.tasks.tasks.logic.loop_task import LoopTask
from ecpy.testing.tasks.util import CheckTask


@pytest.fixture
def task():
    """Create a task to test the validators.

    """
    class Tester(CheckTask):
            """Class for testing feval validators.

            """
            feval = Unicode()

    root = RootTask(should_stop=Event(), should_pause=Event())
    task = Tester(name='test', database_entries={'val': 1})
    loop = LoopTask(name='Loop', task=task)
    root.add_child_task(0, loop)
    return task


def test_base_validation(task):
    """Test simply validating the evaluation.

    """
    task.feval = '2*{test_val}'
    val, res, msg = validators.Feval().check(task, 'feval')
    assert val == 2
    assert res
    assert not msg

    task.feval = '2-*{test_val}'
    val, res, msg = validators.Feval().check(task, 'feval')
    assert val is None
    assert not res
    assert msg


def test_type_validation(task):
    """Test type validating an entry.

    """
    validator = validators.Feval(types=numbers.Real)

    task.feval = '2*{test_val}'
    val, res, msg = validator.check(task, 'feval')
    assert val == 2
    assert res
    assert not msg

    task.feval = '2j*{test_val}'
    val, res, msg = validator.check(task, 'feval')
    assert val is None
    assert not res
    assert msg


def test_warn_on_error(task):
    """Test simply warning on error.

    """
    task.feval = '2-*{test_val}'
    val, res, msg = validators.Feval(warn=True).check(task, 'feval')
    assert val is None
    assert res
    assert msg


def test_skip_empty(task):
    """Test skipping an empty value.

    """
    task.feval = '2*{test_val}'
    val, res, msg = validators.SkipEmpty().check(task, 'feval')
    assert val == 2
    assert res
    assert not msg

    task.feval = ''
    val, res, msg = validators.SkipEmpty().check(task, 'feval')
    assert val is None
    assert res
    assert not msg


def test_skip_in_loop(task):
    """Skip testing the field if the task is embedded in a LoopTask.

    """
    task.feval = ''
    val, res, msg = validators.SkipLoop().check(task, 'feval')
    assert val is None
    assert res
    assert not msg

    task.feval = '2*{test_val}'
    root = task.root
    task.parent.task = None
    root.add_child_task(0, task)
    val, res, msg = validators.SkipLoop().check(task, 'feval')
    assert val == 2
    assert res
    assert not msg
