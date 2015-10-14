# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
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

from ecpy.measure.base_tool import BaseMeasureTool

from .test_measure import measure


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


def test_default_linking(measure):
    """Test default linking to measure.

    """
    tool = ToolTester()
    tool.link_to_measure(measure)
    assert tool.measure
    tool.unlink_from_measure()
    assert not tool.measure
