# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test measurement plugin capabilities.

"""
import os

import pytest
import enaml

from exopy.testing.util import set_preferences, ErrorDialogException

with enaml.imports():
    from exopy.testing.measurement.contributions import MeasureTestManifest


def test_lifecycle(measurement_workbench, app_dir):
    """Test the basic operations performed when starting, living, stopping.

    This includes :

      - check that contributions are properly loaded.
      - check that public are correctly updated.

    """
    plugin = measurement_workbench.get_plugin('exopy.measurement')

    assert plugin.path == os.path.join(app_dir, 'measurement',
                                       'saved_measurements')
    assert os.path.isdir(plugin.path)

    assert plugin.engines
    assert plugin.pre_hooks
    assert plugin.monitors
    assert plugin.default_monitors == ['exopy.text_monitor']

    measurement_workbench.register(MeasureTestManifest())

    for c in ['editors', 'engines', 'pre_hooks', 'post_hooks', 'monitors']:
        assert 'dummy' in getattr(plugin, c)

    measurement_workbench.unregister('exopy.measurement')


def test_getting_declarations(measurement_workbench):
    """Test accessing some declarations through the plugin.

    """
    plugin = measurement_workbench.get_plugin('exopy.measurement')

    for c in ['editor', 'engine', 'pre-hook', 'post-hook', 'monitor']:
        names = sorted(getattr(plugin, c.replace('-', '_')+'s'))
        assert sorted(plugin.get_declarations(c, names).keys()) == names

    with pytest.raises(ValueError):
        plugin.get_declarations('test', [])


def test_creating_tools(measurement_workbench):
    """Test creating tools.

    """
    plugin = measurement_workbench.get_plugin('exopy.measurement')
    measurement_workbench.register(MeasureTestManifest())

    for c in ['editor', 'engine', 'pre-hook', 'post-hook', 'monitor']:
        assert plugin.create(c, 'dummy')

    with pytest.raises(ValueError):
        plugin.create('', 'dummy')

    with pytest.raises(ValueError):
        plugin.create('monitor', '')


def test_selecting_engine(measurement_workbench):
    """Test selecting and unselecting an engine.

    """
    measurement_workbench.register(MeasureTestManifest())
    plugin = measurement_workbench.get_plugin('exopy.measurement')

    decl = plugin.get_declarations('engine', ['dummy'])['dummy']

    plugin.selected_engine = 'dummy'
    assert decl.selected
    plugin.selected_engine = ''
    assert not decl.selected


def test_starting_with_a_default_selected_engine(measurement_workbench):
    """Test that an engine selected by default is well mounted.

    """
    measurement_workbench.register(MeasureTestManifest())
    set_preferences(measurement_workbench,
                    {'exopy.measurement': {'selected_engine': 'dummy'}})

    plugin = measurement_workbench.get_plugin('exopy.measurement')

    decl = plugin.get_declarations('engine', ['dummy'])['dummy']

    assert plugin.selected_engine == 'dummy'
    assert decl.selected


def test_starting_with_default_tools(measurement_workbench):
    """Test staring with default selected tools.

    """
    measurement_workbench.register(MeasureTestManifest())
    set_preferences(measurement_workbench,
                    {'exopy.measurement': {'default_monitors': "['dummy']"}})

    plugin = measurement_workbench.get_plugin('exopy.measurement')

    assert plugin.default_monitors


def test_handling_not_found_default_tools(measurement_workbench):
    """Test handling the non-dectection of default tools.

    """
    set_preferences(measurement_workbench,
                    {'exopy.measurement': {'default_monitors': "['dummy']"}})

    with pytest.raises(ErrorDialogException):
        measurement_workbench.get_plugin('exopy.measurement')


def test_find_next_measurement(measurement_workbench):
    """Test finding the next valid measurement in the queue.

    """
    from exopy.testing.measurement.fixtures import measurement
    m1 = measurement(measurement_workbench)
    m2 = measurement(measurement_workbench)
    m3 = measurement(measurement_workbench)
    plugin = measurement_workbench.get_plugin('exopy.measurement')
    plugin.enqueued_measurements.add(m1)
    plugin.enqueued_measurements.add(m2)
    plugin.enqueued_measurements.add(m3)

    m1.status = 'COMPLETED'
    assert plugin.find_next_measurement() is m2
