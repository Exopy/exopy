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
from pkg_resources import EntryPoint

from ecpy.__main__ import ArgParser, main
from ecpy.testing.util import handle_dialog, process_app_events


pytest_plugins = str('ecpy.testing.fixtures'),


def test_parser_add_argument():
    """Test adding an argument to the parser.

    """
    parser = ArgParser()
    parser.add_argument("--nocapture",
                        help="Don't capture stdout/stderr",
                        action='store_false')
    vals = parser.parse_args('--nocapture'.split(' '))
    assert not vals.nocapture

    with pytest.raises(ValueError):
        parser.add_argument('dummy')


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
    assert vals.workspace == 'ecpy.measure.workspace'

    vals = parser.parse_args('-w ecpy.measure.dummy'.split(' '))
    assert vals.workspace == 'ecpy.measure.dummy'


def test_running_main_error_in_loading(windows, monkeypatch):
    """Test starting the main app but encountering an error while loading
    modifier.

    """
    import ecpy.__main__ as em

    def false_iter(arg):

        class FalseEntryPoint(EntryPoint):
            def load(self, *args, **kwargs):
                raise Exception("Can't load entry point")

        return [FalseEntryPoint('dummy', 'dummy')]

    monkeypatch.setattr(em, 'iter_entry_points', false_iter)

    def check_dialog(dial):
        assert 'extension' in dial.text

    with pytest.raises(SystemExit):
        with handle_dialog('reject', check_dialog):
            main([])


def test_running_main_error_in_parser_modifying(windows, monkeypatch):
    """Test starting the main app but encountering an issue while adding
    arguments.

    """
    import ecpy.__main__ as em

    def false_iter(arg):

        class FalseEntryPoint(EntryPoint):
            def load(self, *args, **kwargs):

                def false_modifier(parser):
                    raise Exception('Failed to add stupid argument to parser')

                return (false_modifier, 1)

        return [FalseEntryPoint('dummy', 'dummy')]

    monkeypatch.setattr(em, 'iter_entry_points', false_iter)

    def check_dialog(dial):
        assert 'modifying' in dial.text

    with pytest.raises(SystemExit):
        with handle_dialog('reject', check_dialog):
            main([])


def test_running_main_error_in_parsing(windows):
    """Test starting the main app but encountering an issue while adding
    arguments.

    """
    def check_dialog(dial):
        assert 'cmd' in dial.text

    with pytest.raises(SystemExit):
        with handle_dialog('reject', check_dialog):
            main(['dummy'])


def test_running_main_error_in_app_startup(windows, monkeypatch):
    """Test starting the main app but encountering an issue when running
    startups.

    """
    from ecpy.app.app_plugin import AppPlugin

    def false_run_startup(self, args):
        raise Exception('Fail to run start up')

    monkeypatch.setattr(AppPlugin, 'run_app_startup', false_run_startup)

    def check_dialog(dial):
        assert 'starting' in dial.text

    with pytest.raises(SystemExit):
        with handle_dialog('reject', check_dialog):
            main([])


def test_running_main(app, app_dir, windows, dialog_sleep, monkeypatch):
    """Test starting the main app and closing it.

    """
    from enaml.workbench.ui.ui_plugin import UIPlugin

    def wait_for_window(self):

        process_app_events(2)
        time.sleep(dialog_sleep)
        self.window.close()

    monkeypatch.setattr(UIPlugin, 'start_application', wait_for_window)
    main([])
