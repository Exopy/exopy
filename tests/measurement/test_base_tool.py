# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the basic tools functionality.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Int

from exopy.measurement.base_tool import BaseMeasureTool, BaseToolDeclaration


class ToolTester(BaseMeasureTool):

    test = Int().tag(pref=True)


def test_check():
    """Test that by default checks pass.

    """
    res, _ = ToolTester().check(None)
    assert res


def test_state_handling():
    """Test basic getting/setting state.

    """
    tool = ToolTester()
    tool.test = 1
    state = tool.get_state()
    assert state['test'] == '1'

    tool.test = 2
    tool.set_state(state)
    assert tool.test == 1


def test_default_linking(measurement):
    """Test default linking to measurement.

    """
    tool = ToolTester()
    tool.link_to_measurement(measurement)
    assert tool.measurement
    tool.unlink_from_measurement()
    assert not tool.measurement


def test_has_view():
    """Test that the has_view member of a BaseToolDeclaration is correctly set.

    """
    class D(BaseToolDeclaration):
        pass

    assert not D().has_view

    class D2(BaseToolDeclaration):
        def make_view(self, tool):
            pass

    assert D2().has_view
