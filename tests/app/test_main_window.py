# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""App plugin extensions declarations.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
import enaml
from enaml.workbench.workbench import Workbench

from ecpy.testing.util import process_app_events

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from enaml.workbench.ui.ui_manifest import UIManifest
    from ecpy.app.errors.manifest import ErrorsManifest
    from ecpy.app.app_manifest import AppManifest
    from .app_helpers import (ClosingContributor1, ClosedContributor)


@pytest.fixture
def workbench_and_tools(windows):
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


def test_app_window(workbench_and_tools):
    """Test that closing and closed handlers are called when trying to close
    the app window.

    """
    w, closing, closed = workbench_and_tools

    ui = w.get_plugin('enaml.workbench.ui')
    ui.show_window()
    process_app_events()

    ui.close_window()
    process_app_events()

    assert closing.called
    assert ui.window.visible

    closing.accept = True
    ui.close_window()
    process_app_events()

    assert not ui.window.visible
    assert closed.called
