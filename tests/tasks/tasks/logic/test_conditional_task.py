# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test of the conditional task.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
import enaml
from multiprocessing import Event

from ecpy.tasks.base_tasks import RootTask
from ecpy.tasks.tasks.logic.conditional_task import ConditionalTask
with enaml.imports():
    from ecpy.tasks.tasks.logic.views.conditional_view import ConditionalView

from ...execution_testing import CheckTask
from ....util import show_and_close_widget


class TestConditionTask(object):
    """Test ConditionalTask.

    """

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = ConditionalTask(name='Test')
        self.root.add_child_task(0, self.task)
        self.check = CheckTask(name='check')
        self.task.add_child_task(0, self.check)

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


@pytest.mark.ui
def test_view(windows):
    """Test the ConditionalTask view.

    """
    show_and_close_widget(ConditionalView(task=ConditionalTask(name='Test')))
