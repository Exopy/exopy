# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test of the WhileTask.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from multiprocessing import Event

import pytest
import enaml

from exopy.testing.util import show_and_close_widget
from exopy.testing.tasks.util import CheckTask
from exopy.tasks.api import RootTask
from exopy.tasks.tasks.logic.while_task import WhileTask
from exopy.tasks.tasks.logic.loop_exceptions_tasks\
    import BreakTask, ContinueTask

with enaml.imports():
    from exopy.tasks.tasks.logic.views.while_view\
        import WhileView


class TestWhileTask(object):
    """The Whiletask behaviour.

    """

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = WhileTask(name='Test')
        self.root.add_child_task(0, self.task)
        self.check = CheckTask(name='check')
        self.task.add_child_task(0, self.check)

    def test_check1(self):
        """Simply test that everything is ok if condition is evaluable.

        """
        self.task.condition = 'True'

        test, traceback = self.task.check()
        assert test
        assert not traceback
        assert self.check.check_called

    def test_check2(self):
        """Test handling a wrong condition.

        """
        self.task.condition = '*True'

        test, traceback = self.task.check(test_instr=True)
        assert not test
        assert len(traceback) == 1
        assert 'root/Test-condition' in traceback

    def test_perform1(self):
        """Test performing when condition is True.

        """
        self.task.condition = '{Test_index} < 5'

        self.root.prepare()

        self.task.perform()
        assert self.check.perform_called == 4

    def test_perform2(self):
        """Test performing when condition is False.

        """
        self.task.condition = '1 < 0'

        self.root.prepare()

        self.task.perform()
        assert not self.check.perform_called

    def test_perform3(self):
        """Test handling of BreakTask and ContinueTask.

        """
        self.task.condition = 'True'
        self.task.add_child_task(0, BreakTask(name='Break',
                                              condition='True'))
        self.task.add_child_task(0, ContinueTask(name='Continue',
                                                 condition='{Test_index} < 5'))

        self.root.prepare()

        self.task.perform()
        assert not self.check.perform_called
        assert self.task.get_from_database('Test_index') == 5

    @pytest.mark.timeout(1)
    def test_perform4(self):
        """Test handling stopping while iterating.

        """
        self.task.condition = 'True'
        stop = lambda t, v: t.root.should_stop.set()
        self.task.add_child_task(0, CheckTask(name='Stop', custom=stop,
                                              stoppable=False))
        self.root.prepare()

        self.task.perform()

        assert self.task.children[0].perform_called == 1


@pytest.mark.ui
def test_while_view(windows):
    """Test the ContinueTask view.

    """
    show_and_close_widget(WhileView(task=WhileTask(name='Test')))
