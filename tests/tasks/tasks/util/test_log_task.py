# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test of the Log task.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
import enaml
from multiprocessing import Event

from ecpy.tasks.base_tasks import RootTask
from ecpy.tasks.tasks.util.log_task import LogTask
with enaml.imports():
    from ecpy.tasks.tasks.util.views.log_view import LogView

from ecpy.testing.tasks.util import CheckTask
from ecpy.testing.util import show_and_close_widget


class TestSleepTask(object):
    """Test LogTask.

    """

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = LogTask(name='Test')
        self.root.add_child_task(0, self.task)
        self.check = CheckTask(name='check')

    def test_perform1(self):
        """Test checking that the message value gets written to the database

        """
        self.task.message = 'TestMessage'
        self.root.prepare()

        self.task.perform()
        assert self.task.get_from_database('Test_message') == 'TestMessage'


@pytest.mark.ui
def test_view(windows):
    """Test the LogTask view.

    """
    show_and_close_widget(LogView(task=LogTask(name='Test')))
