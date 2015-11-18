# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test widgets used to edit text monitor rules.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from time import sleep

import pytest
import enaml

from ecpy.testing.util import process_app_events

with enaml.imports():
    from ecpy.measure.monitors.text_monitor.rules.edition_views\
         import CreateRuleDialog, EditRulesView


pytest_plugins = str('ecpy.testing.measure.monitors.text_monitor.fixtures'),


def test_rule_creation_dialog(text_monitor_workbench, dialog_sleep):
    """
    """
    p = text_monitor_workbench.get_plugin('ecpy.measure.monitors.text_monitor')

    d = CreateRuleDialog(plugin=p)
    d.show()
    process_app_events()
    sleep(dialog_sleep)

    # Select rule type

    # Parametrize rule

    # Choose whether or not to save (use a parametrization of the test function)

    # Check the created rule


def test_rule_edition_dialog(text_monitor_workbench):
    """
    """
     p = text_monitor_workbench.get_plugin('ecpy.measure.monitors.text_monitor')
     m = p.create_monitor(False)

    d = EditRulesView(monitor=m)
    d.show()
    process_app_events()
    sleep(dialog_sleep)

    # Create a new rule

    # Edit the rule

    # Save rule and save and add to default

    # Delete rule
