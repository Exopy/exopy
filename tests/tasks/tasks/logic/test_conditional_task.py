# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test of the conditional task.

"""
import gc

import pytest
import enaml
from multiprocessing import Event

from exopy.testing.tasks.util import CheckTask
from exopy.testing.util import show_and_close_widget
from exopy.tasks.api import RootTask
from exopy.tasks.tasks.logic.conditional_task import ConditionalTask
with enaml.imports():
    from exopy.tasks.tasks.logic.views.conditional_view import ConditionalView


class TestConditionTask(object):
    """Test ConditionalTask.

    """

    def setup_method(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = ConditionalTask(name='Test')
        self.root.add_child_task(0, self.task)
        self.check = CheckTask(name='check')
        self.task.add_child_task(0, self.check)

    def teardown_method(self):
        del self.root.should_pause
        del self.root.should_stop
        # Ensure we collect the file descriptor of the events. Otherwise we can
        # get funny errors on MacOS.
        gc.collect()

    def test_check1(self):
        """Test that everything is ok if condition is evaluable.

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
        self.task.condition = 'True'
        self.root.prepare()

        self.task.perform()
        assert self.check.perform_called

    def test_perform2(self):
        """Test performing when condition is False.

        """
        self.task.condition = '1 < 0'
        self.root.prepare()

        self.task.perform()
        assert not self.check.perform_called

    def test_perform3(self):
        """Test performing when condition is False.

        """
        self.task.condition = 'False'
        self.root.prepare()

        self.task.perform()
        assert not self.check.perform_called


@pytest.mark.ui
def test_view(exopy_qtbot):
    """Test the ConditionalTask view.

    """
    show_and_close_widget(exopy_qtbot,
                          ConditionalView(task=ConditionalTask(name='Test')))
