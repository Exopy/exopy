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

from ecpy.testing.util import show_and_close_widget


class TestSleepTask(object):
    """Test SleepTask.

    """

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = SleepTask(name='Test')
        self.root.add_child_task(0, self.task)

    def test_check1(self):
        """ Test handling a correct string in the 'time' field

        """
        self.task.time = '2.0'

        test, traceback = self.task.check()
        assert test
        assert not traceback
        assert self.task.get_from_database('Test_time') == 2

    def test_check2(self):
        """Test handling a wrong string in the 'time' field.

        """
        self.task.time = 'a1.0'

        test, traceback = self.task.check()
        assert not test
        assert len(traceback) == 1
        assert 'root/Test-time' in traceback

    def test_check3(self):
        """Test handling a negative value 'time' field.

        """
        self.task.time = '-1.0'

        test, traceback = self.task.check()
        assert not test
        assert len(traceback) == 1
        assert 'root/Test' in traceback

    def test_perform1(self):
        """Test performing when 'time' is correctly formatted, and
        checking that the time value gets written to the database

        """
        self.task.time = '1.0+5.0'
        self.root.prepare()

        self.task.perform()
        assert self.task.get_from_database('Test_time') == 6.0


@pytest.mark.ui
def test_view(windows):
    """Test the SleepTask view.

    """
    show_and_close_widget(SleepView(task=SleepTask(name='Test')))
