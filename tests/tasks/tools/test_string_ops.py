# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the string formatting and evaluation performed by the tasks.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from ecpy.tasks.base_tasks import RootTask
from math import cos
import numpy
from numpy.testing import assert_array_equal


class TestFormatting(object):
    """Test formatting strings and caching in running mode.

    """

    def setup(self):
        self.root = RootTask()
        database = self.root.database
        database.set_value('root', 'val1', 1)
        database.create_node('root', 'node1')
        database.set_value('root/node1', 'val2', 10.0)
        database.add_access_exception('root', 'root/node1', 'val2')

    def test_formatting_editing_mode1(self):
        """Test formatting values with text on both sides of expression.

        """
        test = 'progress is {val1}/{val2}, it is good.'
        formatted = self.root.format_string(test)
        assert formatted == 'progress is 1/10.0, it is good.'
        assert not self.root._format_cache

    def test_formatting_editing_mode2(self):
        """Test formatting values with text only on the left of expression.

        """
        test = 'progress is {val1}/{val2}'
        formatted = self.root.format_string(test)
        assert formatted == 'progress is 1/10.0'
        assert not self.root._format_cache

    def test_formatting_editing_mode3(self):
        """Test formatting values with text only on the right of expression.

        """
        test = '{val1}/{val2}, it is good.'
        formatted = self.root.format_string(test)
        assert formatted == '1/10.0, it is good.'
        assert not self.root._format_cache

    def test_formatting_editing_mode4(self):
        """Test formatting values with no other text.

        """
        test = '{val1}/{val2}'
        formatted = self.root.format_string(test)
        assert formatted == '1/10.0'
        assert not self.root._format_cache

    def test_formatting_editing_mode5(self):
        """Test formatting when there is only text.

        """
        test = 'test'
        formatted = self.root.format_string(test)
        assert formatted == 'test'
        assert not self.root._format_cache

    def test_formatting_running_mode1(self):
        """Test formatting values with text on both sides of expression.

        """
        self.root.database.prepare_to_run()
        test = 'progress is {val1}/{val2}, it is good.'
        formatted = self.root.format_string(test)
        assert formatted == 'progress is 1/10.0, it is good.'
        assert self.root._format_cache
        assert test in self.root._format_cache
        self.root.database.set_value('root', 'val1', 2)
        formatted = self.root.format_string(test)
        assert formatted == 'progress is 2/10.0, it is good.'

    def test_formatting_running_mode2(self):
        """Test formatting values with text only on the left of expression.

        """
        self.root. database.prepare_to_run()
        test = 'progress is {val1}/{val2}'
        formatted = self.root.format_string(test)
        assert formatted == 'progress is 1/10.0'
        assert self.root._format_cache
        assert test in self.root._format_cache
        self.root.database.set_value('root', 'val1', 2)
        formatted = self.root.format_string(test)
        assert formatted == 'progress is 2/10.0'

    def test_formatting_running_mode3(self):
        """Test formatting values with text only on the right of expression.

        """
        self.root.database.prepare_to_run()
        test = '{val1}/{val2}, it is good.'
        formatted = self.root.format_string(test)
        assert formatted == '1/10.0, it is good.'
        assert self.root._format_cache
        assert test in self.root._format_cache
        self.root.database.set_value('root', 'val1', 2)
        formatted = self.root.format_string(test)
        assert formatted == '2/10.0, it is good.'

    def test_formatting_running_mode4(self):
        """Test formatting values with no other text.

        """
        self.root.database.prepare_to_run()
        test = '{val1}/{val2}'
        formatted = self.root.format_string(test)
        assert formatted == '1/10.0'
        assert self.root._format_cache
        assert test in self.root._format_cache
        self.root.database.set_value('root', 'val1', 2)
        formatted = self.root.format_string(test)
        assert formatted == '2/10.0'

    def test_formatting_running_mode5(self):
        """Test formatting when there is only text.

        """
        self.root.database.prepare_to_run()
        test = 'test'
        formatted = self.root.format_string(test)
        assert formatted == 'test'
        assert self.root._format_cache
        assert test in self.root._format_cache


class TestEvaluation(object):
    """Test evaluating strings and caching in running mode.

    """

    def setup(self):
        self.root = RootTask()
        database = self.root.database
        database.set_value('root', 'val1', 1)
        database.create_node('root', 'node1')
        database.set_value('root/node1', 'val2', 10.0)
        database.add_access_exception('root', 'root/node1', 'val2')

    def test_eval_pure_string_editing_mode(self):
        """Test evaluating a word.

        """
        test = 'test'
        formatted = self.root.format_and_eval_string(test)
        assert formatted == 'test'

    def test_eval_editing_mode1(self):
        """Test eval expression with only standard operators.

        """
        test = '{val1}/{val2}'
        formatted = self.root.format_and_eval_string(test)
        assert formatted == 0.1
        assert not self.root._eval_cache

    def test_eval_editing_mode2(self):
        """Test eval expression containing a math function.

        """
        test = 'cos({val1}/{val2})'
        formatted = self.root.format_and_eval_string(test)
        assert formatted == cos(0.1)
        assert not self.root._eval_cache

    def test_eval_editing_mode3(self):
        """Test eval expression containing a cmath function.

        """
        self.root.database.set_value('root', 'val1', 10.0)
        test = 'cm.sqrt({val1}/{val2})'
        formatted = self.root.format_and_eval_string(test)
        assert formatted == 1+0j
        assert not self.root._eval_cache

    def test_eval_editing_mode4(self):
        """Test eval expression containing a numpy function.

        """
        self.root.database.set_value('root', 'val1', [1.0, -1.0])
        test = 'np.abs({val1})'
        formatted = self.root.format_and_eval_string(test)
        assert_array_equal(formatted, numpy.array((1.0, 1.0)))
        assert not self.root._eval_cache

    def test_eval_pure_string_running_mode(self):
        """Test evaluating a word.

        """
        self.root.database.prepare_to_run()
        test = 'test'
        formatted = self.root.format_and_eval_string(test)
        assert formatted == 'test'

    def test_eval_running_mode1(self):
        """Test eval expression with only standard operators.

        """
        self.root.database.prepare_to_run()
        test = '{val1}/{val2}'
        formatted = self.root.format_and_eval_string(test)
        assert formatted == 0.1
        assert self.root._eval_cache
        assert test in self.root._eval_cache
        self.root.database.set_value('root', 'val1', 2)
        formatted = self.root.format_and_eval_string(test)
        assert formatted == 0.2

    def test_eval_running_mode2(self):
        """Test eval expression containing a math function.

        """
        self.root.database.prepare_to_run()
        test = 'cos({val1}/{val2})'
        formatted = self.root.format_and_eval_string(test)
        assert formatted == cos(0.1)
        assert self.root._eval_cache
        assert test in self.root._eval_cache
        self.root.database.set_value('root', 'val1', 2)
        formatted = self.root.format_and_eval_string(test)
        assert formatted == cos(0.2)

    def test_eval_running_mode3(self):
        """Test eval expression containing a cmath function.

        """
        self.root.database.prepare_to_run()
        self.root.database.set_value('root', 'val1', 10.0)
        test = 'cm.sqrt({val1}/{val2})'
        formatted = self.root.format_and_eval_string(test)
        assert formatted == (1+0j)
        assert self.root._eval_cache
        assert test in self.root._eval_cache
        self.root.database.set_value('root', 'val1', 40.0)
        formatted = self.root.format_and_eval_string(test)
        assert formatted == (2+0j)

    def test_eval_running_mode4(self):
        """Test eval expression containing a numpy function.

        """
        self.root.database.prepare_to_run()
        self.root.database.set_value('root', 'val1', [1.0, -1.0])
        test = 'np.abs({val1})'
        formatted = self.root.format_and_eval_string(test)
        assert_array_equal(formatted, numpy.array((1.0, 1.0)))
        assert self.root._eval_cache
        assert test in self.root._eval_cache
        self.root.database.set_value('root', 'val1', [2.0, -1.0])
        self.root.database.set_value('root', 'val2', 0)
        test = 'np.abs({val1})[{val2}]'
        formatted = self.root.format_and_eval_string(test)
        assert formatted == 2.0
