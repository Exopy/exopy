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

    # Test updating of public members

    measure_workbench.unregister('ecpy.measure')


def test_getting_declarations(measure_workbench):
    """Test accessing some declarations through the plugin.

    """
    plugin = measure_workbench.get_plugin('ecpy.measure')

    assert (plugin.get_declarations('engine', plugin.engines).keys() ==
            plugin.engines)

    with pytest.raises(ValueError):
        plugin.get_declarations('test', [])


def test_creating_tools(measure_workbench):
    """Test creating tools.

    """
    plugin = measure_workbench.get_plugin('ecpy.measure')
    measure_workbench.register(MeasureTestManifest())

    for c in ['editor', 'engine', 'pre_hook', 'post_hook', 'monitor']:
        assert plugin.create(c, 'dummy')

    with pytest.raises(ValueError):
        plugin.create('', 'dummy')

    with pytest.raises(ValueError):
        plugin.create('monitor', 'dummy')


def test_selecting_engine(measure_workbench):
    """
    """
    pass


def test_starting_with_a_default_selected_engine(measure_workbench):
    """
    """
    pass


def test_handling_not_found_default_tools(measure_workbench):
    """
    """
    pass
