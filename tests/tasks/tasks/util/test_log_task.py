# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test of the Log task.

"""
import pytest
import enaml
from multiprocessing import Event

from exopy.testing.util import show_and_close_widget
from exopy.tasks.tasks.base_tasks import RootTask
from exopy.tasks.tasks.util.log_task import LogTask
with enaml.imports():
    from exopy.tasks.tasks.util.views.log_view import LogView


class TestLogTask(object):
    """Test LogTask.

    """

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = LogTask(name='Test')
        self.root.add_child_task(0, self.task)

    def test_check1(self):
        """Test checking that a message that cannot be formatted will result in a fail

        """
        self.task.message = 'TestMessage {aa}'

        test, traceback = self.task.check()

        assert not test
        assert len(traceback) == 1
        assert 'root/Test-message' in traceback
        assert not self.task.get_from_database('Test_message')

    def test_perform1(self):
        """Test checking that the message value gets written to the database

        """
        self.task.write_in_database('val', 'World')
        self.task.message = 'Hello {Test_val}'
        self.root.prepare()

        self.task.perform()
        assert self.task.get_from_database('Test_message') == 'Hello World'


@pytest.mark.ui
def test_view(exopy_qtbot):
    """Test the LogTask view.

    """
    show_and_close_widget(exopy_qtbot, LogView(task=LogTask(name='Test')))
