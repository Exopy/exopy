# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test application startup script.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import time

import pytest

from ecpy.ecpy import ArgParser, main


pytest_plugins = str('ecpy.testing.fixtures'),


def test_parser_add_argument():
    """Test adding an argument to the parser.

    """
    parser = ArgParser()
    parser.add_argument("-s", "--nocapture",
                        help="Don't capture stdout/stderr",
                        action='store_false')
    vals = parser.parse_args('-s'.split(' '))
    assert not vals.nocapture


def test_parser_adding_choice_and_arg_with_choice():
    """Test adding a choice and an argument relying on the choice.

    """
    parser = ArgParser()
    parser.add_choice('workspaces', 'ecpy.measure.workspace', 'measure')
    parser.add_argument("-w", "--workspace",
                        help='Select start-up workspace',
                        default='measure', choices='workspaces')
    parser.add_choice('workspaces', 'ecpy.measure.dummy', 'measure')

    vals = parser.parse_args('-w measure'.split(' '))
    assert vals.workspace == 'measure'
    assert parser.choices['workspaces']['measure'] == 'ecpy.measure.workspace'

    vals = parser.parse_args('-w ecpy.measure.dummy'.split(' '))
    assert vals.workspace == 'ecpy.measure.dummy'


def test_running_main_error_in_loading(windows, dialog_sleep, monkeypatch):
    """Test starting the main app but encountering an error while loading
    modifier.

    """
    pass


def test_running_main_error_in_parser_modifying(windows, dialog_sleep,
                                                monkeypatch):
    """Test starting the main app but encountering an issue while adding
    arguments.

    """
    pass


def test_running_main_error_in_app_startup(windows, dialog_sleep,
                                           monkeypatch):
    """Test starting the main app but encountering an issue when running
    startups.

    """
    pass


def test_running_main(windows, dialog_sleep):
    """Test starting the main app and closing it.

    """
    pass
