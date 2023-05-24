# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test of the Formula task.

"""
import gc

import pytest
import enaml
from multiprocessing import Event
from collections import OrderedDict

from exopy.testing.util import show_and_close_widget
from exopy.tasks.tasks.base_tasks import RootTask
from exopy.tasks.tasks.util.formula_task import FormulaTask
from exopy.utils.atom_util import (ordered_dict_from_pref)
with enaml.imports():
    from exopy.tasks.tasks.util.views.formula_view import FormulaView


class TestFormulaTask(object):
    """Test FormulaTask.

    """

    def setup_method(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = FormulaTask(name='Test')
        self.root.add_child_task(0, self.task)

    def teardown_method(self):
        del self.root.should_pause
        del self.root.should_stop
        # Ensure we collect the file descriptor of the events. Otherwise we can
        # get funny errors on MacOS.
        gc.collect()

    def test_perform1(self):
        """Test checking that the evaluated formula gets written to the
        database

        """
        self.task.formulas = OrderedDict([('key1', "1.0+3.0"),
                                          ('key2', '3.0+4.0')])
        self.root.prepare()

        self.task.perform()
        assert (self.task.get_from_database('Test_key1') == 4.0 and
                self.task.get_from_database('Test_key2') == 7.0)

    def test_perform_from_load(self):
        """Test checking for correct loading from pref and that we can still
        recall values from the database

        """
        self.task.write_in_database('pi', 3.1)
        self.task.formulas = \
            ordered_dict_from_pref(self, self.task.formulas,
                                   ("[(u'key1', '1.0+3.0'), "
                                    "(u'key2', '3.0 + {Test_pi}')]"))
        self.root.prepare()

        self.task.perform()
        assert (self.task.get_from_database('Test_key1') == 4.0 and
                self.task.get_from_database('Test_key2') == 6.1)

    def test_check(self):
        """Test checking that an unformattable formula gives an error

        """
        self.task.formulas = OrderedDict([('key1', "1.0+3.0"),
                                          ('key2', '3.0+4.0 + {Test_pi}')])

        test, traceback = self.task.check()
        assert not test
        assert len(traceback) == 1
        assert 'root/Test-key2' in traceback


@pytest.mark.ui
def test_view(exopy_qtbot):
    """Test the FormulaTask view.

    """
    show_and_close_widget(exopy_qtbot,
                          FormulaView(task=FormulaTask(name='Test')))
