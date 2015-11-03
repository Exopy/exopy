# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test measure plugin capabilities.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
import enaml

from ..util import set_preferences, ErrorDialogException

with enaml.imports():
    from .contributions import MeasureTestManifest


def test_lifecycle(measure_workbench):
    """Test the basic opertaions performed when starting, living, stopping.

    This includes :

      - check that contributions are properly loaded.
      - check that public are correctly updated.

    """
    plugin = measure_workbench.get_plugin('ecpy.measure')

    assert plugin.engines
    assert plugin.pre_hooks

    measure_workbench.register(MeasureTestManifest())

    for c in ['editors', 'engines', 'pre_hooks', 'post_hooks', 'monitors']:
        assert 'dummy' in getattr(plugin, c)

    measure_workbench.unregister('ecpy.measure')


def test_getting_declarations(measure_workbench):
    """Test accessing some declarations through the plugin.

    """
    plugin = measure_workbench.get_plugin('ecpy.measure')

    for c in ['editor', 'engine', 'pre-hook', 'post-hook', 'monitor']:
        names = sorted(getattr(plugin, c.replace('-', '_')+'s'))
        assert sorted(plugin.get_declarations(c, names).keys()) == names

    with pytest.raises(ValueError):
        plugin.get_declarations('test', [])


def test_creating_tools(measure_workbench):
    """Test creating tools.

    """
    plugin = measure_workbench.get_plugin('ecpy.measure')
    measure_workbench.register(MeasureTestManifest())

    for c in ['editor', 'engine', 'pre-hook', 'post-hook', 'monitor']:
        assert plugin.create(c, 'dummy')

    with pytest.raises(ValueError):
        plugin.create('', 'dummy')

    with pytest.raises(ValueError):
        plugin.create('monitor', '')


def test_selecting_engine(measure_workbench):
    """Test selecting and unselecting an engine.

    """
    measure_workbench.register(MeasureTestManifest())
    plugin = measure_workbench.get_plugin('ecpy.measure')

    decl = plugin.get_declarations('engine', ['dummy'])['dummy']

    plugin.selected_engine = 'dummy'
    assert decl.selected
    plugin.selected_engine = ''
    assert not decl.selected


def test_starting_with_a_default_selected_engine(measure_workbench):
    """Test that an engine selected by default is well mounted.

    """
    measure_workbench.register(MeasureTestManifest())
    set_preferences(measure_workbench,
                    {'ecpy.measure': {'selected_engine': 'dummy'}})

    plugin = measure_workbench.get_plugin('ecpy.measure')

    decl = plugin.get_declarations('engine', ['dummy'])['dummy']

    assert plugin.selected_engine == 'dummy'
    assert decl.selected


def test_starting_with_default_tools(measure_workbench):
    """Test staring with default selected tools.

    """
    measure_workbench.register(MeasureTestManifest())
    set_preferences(measure_workbench,
                    {'ecpy.measure': {'default_monitors': "['dummy']"}})

    plugin = measure_workbench.get_plugin('ecpy.measure')

    assert plugin.default_monitors


def test_handling_not_found_default_tools(measure_workbench):
    """Test handling the non-dectection of default tools.

    """
    set_preferences(measure_workbench,
                    {'ecpy.measure': {'default_monitors': "['dummy']"}})

    with pytest.raises(ErrorDialogException):
        measure_workbench.get_plugin('ecpy.measure')


def test_find_next_measure(measure_workbench):
    """Test finding the next valid measure in the queue.

    """
    from .conftest import measure
    m1 = measure(measure_workbench)
    m2 = measure(measure_workbench)
    m3 = measure(measure_workbench)
    plugin = measure_workbench.get_plugin('ecpy.measure')
    plugin.enqueued_measures.add(m1)
    plugin.enqueued_measures.add(m2)
    plugin.enqueued_measures.add(m3)

    m1.status = 'COMPLETED'
    assert plugin.find_next_measure() is m2


def test_validate_closing():
    """
    """
    pass # XXXX