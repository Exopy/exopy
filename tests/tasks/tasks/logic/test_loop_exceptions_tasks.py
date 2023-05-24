# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test of the loop exceptions tasks.

"""
import gc

import pytest
import enaml
from multiprocessing import Event

from exopy.testing.util import show_and_close_widget
from exopy.tasks.api import RootTask
from exopy.tasks.tasks.logic.loop_task import LoopTask
from exopy.tasks.tasks.logic.while_task import WhileTask
from exopy.tasks.tasks.logic.loop_exceptions_tasks\
    import BreakTask, ContinueTask

with enaml.imports():
    from exopy.tasks.tasks.logic.views.loop_exceptions_views\
        import BreakView, ContinueView


@pytest.fixture(params=(BreakTask, ContinueTask))
def exception_task(request):
    return request.param(name='Test')


class TestExceptionTasks(object):
    """Test Break and Continue tasks checks, perform will be tested in each
    looping task

    """

    def setup_method(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())

    def teardown_method(self):
        del self.root.should_pause
        del self.root.should_stop
        # Ensure we collect the file descriptor of the events. Otherwise we can
        # get funny errors on MacOS.
        gc.collect()


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


@pytest.mark.ui
def test_break_view(exopy_qtbot):
    """Test the BreakTask view.

    """
    show_and_close_widget(exopy_qtbot, BreakView(task=BreakTask(name='Test')))


@pytest.mark.ui
def test_continue_view(exopy_qtbot):
    """Test the ContinueTask view.

    """
    show_and_close_widget(exopy_qtbot,
                          ContinueView(task=ContinueTask(name='Test')))
