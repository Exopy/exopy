# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""App plugin extensions declarations.

"""
import pytest
import enaml
from enaml.workbench.workbench import Workbench

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from enaml.workbench.ui.ui_manifest import UIManifest
    from exopy.app.errors.manifest import ErrorsManifest
    from exopy.app.app_manifest import AppManifest
    from .app_helpers import (ClosingContributor1, ClosedContributor)


@pytest.fixture
def workbench_and_tools(exopy_qtbot):
    """Create a workbench to test closing of the application window.

    """
    workbench = Workbench()
    workbench.register(CoreManifest())
    workbench.register(UIManifest())
    workbench.register(AppManifest())
    workbench.register(ErrorsManifest())
    closing = ClosingContributor1()
    workbench.register(closing)
    closed = ClosedContributor()
    workbench.register(closed)

    return workbench, closing, closed


def test_app_window(exopy_qtbot, workbench_and_tools):
    """Test that closing and closed handlers are called when trying to close
    the app window.

    """
    w, closing, closed = workbench_and_tools

    ui = w.get_plugin('enaml.workbench.ui')
    ui.show_window()

    ui.close_window()

    def assert_closing_called():
        assert closing.called
    exopy_qtbot.wait_until(assert_closing_called)
    assert ui.window.visible

    closing.accept = True
    ui.close_window()

    def assert_closed_called():
        assert closed.called
    exopy_qtbot.wait_until(assert_closed_called)
    assert not ui.window.visible
