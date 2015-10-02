# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the measure object capabilities.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
import enaml

from ecpy.measure.measure import Measure
from ecpy.tasks.api import RootTask

with enaml.imports():
    from .contributions import MeasureTestManifest


@pytest.fixture
def measure(measure_workbench):
    """Register the dummy testing tools and create an empty measure.

    """
    measure_workbench.register(MeasureTestManifest())
    plugin = measure_workbench.get_plugin('ecpy.measure')
    measure = Measure(plugin=plugin, root_task=RootTask(),
                      name='Dummy', id='001')
    return measure


@pytest.mark.parametrize('kind', ['pre-hook', 'monitor', 'post-hook'])
def test_tool_handling(measure, kind):
    """Test adding/moving and removing a tool from a measure.

    """
    member = lambda : getattr(measure, kind.replace('-', '_')+'s')

    measure.add_tool(kind, 'dummy')

    assert 'dummy' in member()
    assert member()['dummy'].measure is measure

    with pytest.raises(KeyError):
        measure.add_tool(kind, 'dummy')

    if kind == 'pre-hook':
        assert member().keys()[1] == 'dummy'
        measure.move_tool(kind, 1, 0)
        assert member().keys()[0] == 'dummy'

    measure.remove_tool(kind, 'dummy')
    assert 'dummy' not in member()

    with pytest.raises(KeyError):
        measure.remove_tool(kind, 'dummy')


def test_tool_function_kind_checking(measure):
    """Simply check that kind checking is correctly enforced in all tool
    handling functions.

    """
    for f in ('add_tool', 'remove_tool', 'move_tool'):
        with pytest.raises(ValueError):
            m = getattr(measure, f)
            if f == 'move_tool':
                m('', 0, 1)
            else:
                m('', None)

    with pytest.raises(ValueError):
        measure.move_tool('monitor', 0, 1)


def test_measure_persistence(measure):
    """
    """
    pass  # Test saving loading


def test_running_checks(measure):
    """
    """
    pass


def test_changing_state(measure):
    """
    """
    pass


def test_collecting_observed_entries(measure):
    """
    """
    pass


def test_dependencies_handling(measure):
    """
    """
    pass
