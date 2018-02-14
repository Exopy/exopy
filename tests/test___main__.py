# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test application startup script.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
from pkg_resources import EntryPoint

from exopy.__main__ import ArgParser, main
from exopy.testing.util import handle_dialog


pytest_plugins = str('exopy.testing.fixtures'),


def test_parser_add_argument():
    """Test adding an argument to the parser.

    """
    parser = ArgParser()
    parser.add_argument("--nocapture",
                        help="Don't capture stdout/stderr",
                        action='store_true')
    vals = parser.parse_args('--nocapture'.split(' '))
    assert vals.nocapture

    with pytest.raises(ValueError):
        parser.add_argument('dummy')


def test_parser_adding_choice_and_arg_with_choice():
    """Test adding a choice and an argument relying on the choice.

    """
    parser = ArgParser()
    parser.add_choice('workspaces', 'exopy.measurement.workspace',
                      'measurement')
    parser.add_argument("-w", "--workspace",
                        help='Select start-up workspace',
                        default='measurement', choices='workspaces')
    parser.add_choice('workspaces', 'exopy.measurement.dummy', 'measurement')

    vals = parser.parse_args('-w measurement'.split(' '))
    assert vals.workspace == 'exopy.measurement.workspace'

    vals = parser.parse_args('-w exopy.measurement.dummy'.split(' '))
    assert vals.workspace == 'exopy.measurement.dummy'


def test_running_main_error_in_loading(windows, monkeypatch):
    """Test starting the main app but encountering an error while loading
    modifier.

    """
    import exopy.__main__ as em

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
    import exopy.__main__ as em

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
    from exopy.app.app_plugin import AppPlugin

    def false_run_startup(self, args):
        raise Exception('Fail to run start up')

    monkeypatch.setattr(AppPlugin, 'run_app_startup', false_run_startup)

    def check_dialog(dial):
        assert 'starting' in dial.text

    with pytest.raises(SystemExit):
        with handle_dialog('reject', check_dialog):
            main([])


def test_running_main(app, app_dir, windows, monkeypatch):
    """Test starting the main app and closing it.

    """
    from enaml.workbench.ui.ui_plugin import UIPlugin

    def wait_for_window(self):
        pass

    # Do not release the application
    def no_release(self):
        pass

    monkeypatch.setattr(UIPlugin, '_release_application', no_release)
    monkeypatch.setattr(UIPlugin, 'start_application', wait_for_window)

    import sys
    old = sys.excepthook
    try:
        main([])
    finally:
        sys.excepthook = old


def test_running_main_asking_for_help(app):
    """Test starting the main app and closing it.

    """
    try:
        main(['-h'])
        # TODO make sure no window was opened ?
    except SystemExit as e:
        assert e.args == (0,)
