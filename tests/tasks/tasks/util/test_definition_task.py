# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test of the Definition task.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
import enaml
from multiprocessing import Event
from collections import OrderedDict

from exopy.testing.util import show_and_close_widget
from exopy.tasks.tasks.string_evaluation import safe_eval
from exopy.tasks.tasks.base_tasks import RootTask
from exopy.tasks.tasks.util.definition_task import DefinitionTask
from exopy.utils.atom_util import (ordered_dict_from_pref)

with enaml.imports():
    from exopy.tasks.tasks.util.views.definition_view import DefinitionView


class TestDefinitionTask(object):
    """Test DefinitionTask.

    """

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = DefinitionTask(name='Test')
        self.root.add_child_task(0, self.task)

    def test_perform1(self):
        """Test checking that the formatted definition gets written to the
        database

        """
        self.task.write_in_database('it', 'World')
        self.task.definitions = OrderedDict([('key1', "2.0+3.0"),
                                             ('key2', 'Hello')])
        self.root.prepare()

        self.task.check()
        assert self.task.get_from_database('Test_key1') == safe_eval(
            "1.0+4.0", {})
        assert self.task.get_from_database('Test_key2') == "Hello"

    def test_check_after_load(self):
        """Test checking for correct loading from pref and that we can still
        recall values from the database

        """
        self.task.write_in_database('it', 'World')

        pref = "[(u'key1', u'1.0+3.0'), (u'key2', u'Hello')]"
        self.task.definitions = ordered_dict_from_pref(self,
                                                       self.task.definitions,
                                                       pref)

        self.root.prepare()

        self.task.check()
        assert self.task.get_from_database('Test_key1') == safe_eval(
            "1.0+3.0", {})
        assert self.task.get_from_database('Test_key2') == "Hello"

    def test_check(self):
        """Test checking that an unformattable definition gives an error

        """
        self.task.definitions = OrderedDict([('key1', "1.0+3.0"),
                                             ('key2', '3.0+4.0 + {Test_pi}')])

        test, traceback = self.task.check()
        assert not test
        assert len(traceback) == 1
        assert 'root/Test-key2' in traceback


@pytest.mark.ui
def test_view(windows):
    """Test the FormulaTask view.

    """
    show_and_close_widget(DefinitionView(task=DefinitionTask(name='Test')))
