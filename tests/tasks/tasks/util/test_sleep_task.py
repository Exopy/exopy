# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test of the Sleep task.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
import enaml
from multiprocessing import Event

from ecpy.tasks.base_tasks import RootTask
from ecpy.tasks.tasks.util.sleep_task import SleepTask
with enaml.imports():
    from ecpy.tasks.tasks.util.views.sleep_view import SleepView

from ecpy.testing.tasks.util import CheckTask
from ecpy.testing.util import show_and_close_widget


class TestSleepTask(object):
    """Test SleepTask.

    """

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SleepTask(name='Test')
        self.root.add_child_task(0, self.task)
        self.check = CheckTask(name='check')

    def test_check1(self):
        """ Test handling a correct string in the 'time' field

        """
        self.task.time = '1.0'

        test, traceback = self.task.check()
        assert test
        assert not traceback
        assert self.check.check_called

    def test_check2(self):
        """Test handling a wrong string in the 'time' field.

        """
        self.task.time = 'a1.0'

        test, traceback = self.task.check(test_instr=True)
        assert not test
        assert len(traceback) == 1
        assert 'root/Test-time' in traceback

    def test_perform1(self):
        """Test performing when 'time' is correctly formatted.

        """
        self.task.time = '1.0'
        self.root.prepare()

        self.task.perform()
        assert self.check.perform_called


@pytest.mark.ui
def test_view(windows):
    """Test the ConditionalTask view.

    """
    show_and_close_widget(SleepView(task=SleepTask(name='Test')))

