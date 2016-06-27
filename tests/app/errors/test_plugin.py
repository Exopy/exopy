# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the ErrorsPlugin.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
import enaml
from enaml.widgets.api import MultilineField
from future.utils import python_2_unicode_compatible

from ecpy.testing.util import handle_dialog, get_window, show_and_close_widget

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from enaml.workbench.ui.ui_manifest import UIManifest
    from ecpy.app.app_manifest import AppManifest
    from ecpy.app.errors.manifest import ErrorsManifest
    from ecpy.app.errors.widgets import HierarchicalErrorsDisplay
    from ecpy.app.packages.manifest import PackagesManifest


APP_ID = 'ecpy.app'
ERRORS_ID = 'ecpy.app.errors'


@pytest.fixture
def err_workbench(workbench):
    """Create a workbench and register basic manifests.

    """
    workbench.register(CoreManifest())
    workbench.register(ErrorsManifest())
    workbench.register(PackagesManifest())
    return workbench


@python_2_unicode_compatible
class FailedFormat(object):

    def __str__(self):
        self.called = 1
        raise ValueError()

    def __repr__(self):
        self.called = 1
        raise ValueError()


# =============================================================================
# --- Test plugin -------------------------------------------------------------
# =============================================================================


def test_life_cycle(err_workbench):
    """Test basic behavior of ErrorsPlugin.

    """
    plugin = err_workbench.get_plugin(ERRORS_ID)

    assert len(plugin.errors) == 4

    plugin._errors_handlers.contributions = {}

    assert len(plugin.errors) == 0

    plugin.stop()

    assert not len(plugin.errors)


@pytest.mark.ui
def test_signal_command_with_unknown(err_workbench, windows):
    """Test the signal command with a stupid kind of error.

    """
    core = err_workbench.get_plugin('enaml.workbench.core')

    with handle_dialog():
        core.invoke_command('ecpy.app.errors.signal',
                            {'kind': 'stupid', 'msg': None})

    with handle_dialog():
        fail = FailedFormat()
        core.invoke_command('ecpy.app.errors.signal',
                            {'kind': 'stupid', 'msg': fail})

    assert getattr(fail, 'called', None)


@pytest.mark.ui
def test_handling_error_in_handlers(err_workbench, windows):
    """Test handling an error occuring in a specilaized handler.

    """
    plugin = err_workbench.get_plugin(ERRORS_ID)

    def check_dialog(dial):
        assert 'error' in dial.errors
        assert 'registering' not in dial.errors

    with handle_dialog(custom=check_dialog):
        plugin.signal('registering')

    with handle_dialog(custom=check_dialog):
        plugin.signal('registering', msg=FailedFormat())


@pytest.mark.ui
def test_gathering_mode(err_workbench, windows):
    """Test gathering multiple errors.

    """
    core = err_workbench.get_plugin('enaml.workbench.core')
    core.invoke_command('ecpy.app.errors.enter_error_gathering')

    core.invoke_command('ecpy.app.errors.signal',
                        {'kind': 'stupid', 'msg': None})
    assert get_window() is None

    with handle_dialog():
        core.invoke_command('ecpy.app.errors.exit_error_gathering')


@pytest.mark.ui
def test_report_command(err_workbench, windows):
    """Test generating an application errors report.

    """
    core = err_workbench.get_plugin('enaml.workbench.core')
    with handle_dialog():
        core.invoke_command('ecpy.app.errors.report')

    with handle_dialog():
        core.invoke_command('ecpy.app.errors.report', dict(kind='error'))

    with handle_dialog():
        core.invoke_command('ecpy.app.errors.report', dict(kind='stupid'))


@pytest.mark.ui
def test_install_excepthook(err_workbench, windows):
    """Test the installation and use of the sys.excepthook.

    """
    import sys
    old_hook = sys.excepthook

    err_workbench.register(UIManifest())
    err_workbench.register(AppManifest())
    core = err_workbench.get_plugin('enaml.workbench.core')
    core.invoke_command('ecpy.app.errors.install_excepthook')

    new_hook = sys.excepthook
    sys.excepthook = old_hook

    assert old_hook is not new_hook

    with handle_dialog():
        new_hook(Exception, 'Test', '')


# =============================================================================
# --- Test error handler ------------------------------------------------------
# =============================================================================

def test_reporting_single_error(err_workbench):
    """Check handling a single error.

    """
    plugin = err_workbench.get_plugin('ecpy.app.errors')
    handler = plugin._errors_handlers.contributions['error']

    assert handler.handle(err_workbench, {'message': 'test'})

    assert 'No message' in handler.handle(err_workbench, {}).text


def test_reporting_multiple_errors(err_workbench):
    """Check handling multiple errors.

    """
    plugin = err_workbench.get_plugin('ecpy.app.errors')
    handler = plugin._errors_handlers.contributions['error']

    assert handler.handle(err_workbench, [{'message': 'test'}])

    assert 'No message' in handler.handle(err_workbench, {}).text


# =============================================================================
# --- Test registering handler ------------------------------------------------
# =============================================================================

def test_reporting_single_registering_error(err_workbench):
    """Check handling a single registering error.

    """
    plugin = err_workbench.get_plugin('ecpy.app.errors')
    handler = plugin._errors_handlers.contributions['registering']

    assert handler.handle(err_workbench, {'id': 'test', 'message': 'test'})

    with pytest.raises(Exception):
        handler.handle(err_workbench, {})


def test_reporting_multiple_registering_errors(err_workbench):
    """Check handling multiple package errors.

    """
    plugin = err_workbench.get_plugin('ecpy.app.errors')
    handler = plugin._errors_handlers.contributions['registering']

    assert handler.handle(err_workbench, [{'id': 'test', 'message': 'test'}])

    with pytest.raises(Exception):
        handler.handle(err_workbench, {})


# =============================================================================
# --- Test extensions handler -------------------------------------------------
# =============================================================================

def test_handling_single_extension_error(err_workbench):
    """Check handling a single extension error.

    """
    plugin = err_workbench.get_plugin('ecpy.app.errors')
    handler = plugin._errors_handlers.contributions['extensions']

    assert handler.handle(err_workbench, {'point': 'test', 'errors': {}})

    with pytest.raises(Exception):
        handler.handle(err_workbench, {})


def test_handling_multiple_extension_errors(err_workbench):
    """Check handling multiple extension errors.

    """
    plugin = err_workbench.get_plugin('ecpy.app.errors')
    handler = plugin._errors_handlers.contributions['extensions']

    assert handler.handle(err_workbench, [{'point': 'test', 'errors': {}}])

    with pytest.raises(Exception):
        handler.handle(err_workbench, {})


def test_reporting_on_extension_errors(err_workbench):
    """Check reporting extension errors.

    """
    plugin = err_workbench.get_plugin('ecpy.app.errors')
    handler = plugin._errors_handlers.contributions['extensions']

    widget = handler.report(err_workbench)
    assert isinstance(widget, MultilineField)
    show_and_close_widget(widget)

    handler.errors = {'test': {'errror': 'msg'}}

    widget = handler.report(err_workbench)
    assert isinstance(widget, HierarchicalErrorsDisplay)
    show_and_close_widget(widget)


# =============================================================================
# --- API import --------------------------------------------------------------
# =============================================================================

def test_api_import():
    """Test importing the api module.

    """
    from ecpy.app.errors import api
    assert api.__all__
