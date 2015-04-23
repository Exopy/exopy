# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test of the task interface system.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
from multiprocessing import Event

from ecpy.tasks.base_tasks import RootTask
from ecpy.tasks.tasks.logic.loop_task import LoopTask
from ecpy.tasks.tasks.logic.while_task import WhileTask
from ecpy.tasks.tasks.logic.loop_exceptions_tasks\
    import BreakTask, ContinueTask


@pytest.fixture(params=(BreakTask, ContinueTask))
def exception_task(request):
    return request.param(name='Test')


class TestExceptionTasks(object):
    """Test Break and Continue tasks checks, perform will be tested in each
    looping task

    """

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())

    def test_check1(self, exception_task):
        """Test that everything is ok condition is evaluable and parent
        is a Loop.

        """
        loop = LoopTask()
        loop.add_child_task(0, exception_task)
        self.root.add_child_task(0, loop)
        exception_task.condition = 'True'

        test, traceback = exception_task.check()
        assert test
        assert not traceback

    def test_check2(self, exception_task):
        """Simply test that everything is ok condition is evaluable and parent
        is a While.

        """
        whil = WhileTask()
        whil.add_child_task(0, exception_task)
        exception_task.condition = 'True'
        self.root.add_child_task(0, whil)

        test, traceback = exception_task.check()
        assert test
        assert not traceback

    def test_check3(self, exception_task):
        """Test handling a wrong condition.

        """
        loop = LoopTask(name='Parent')
        loop.add_child_task(0, exception_task)
        exception_task.condition = '*True'
        self.root.add_child_task(0, loop)

        test, traceback = exception_task.check()
        assert not test
        assert len(traceback) == 1
        assert 'root/Parent/Test-condition' in traceback

    def test_check4(self, exception_task):
        """Test handling a wrong parent type.

        """
        self.root.add_child_task(0, exception_task)
        exception_task.condition = 'True'

        test, traceback = exception_task.check()
        assert not test
        assert len(traceback) == 1
        assert 'root/Test-parent' in traceback
