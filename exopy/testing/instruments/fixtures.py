# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Fixture for testing the instruments manager plugin.

"""
from time import sleep

import pytest
import enaml

from exopy.testing.util import exit_on_err

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest

    from exopy.app.app_manifest import AppManifest
    from exopy.app.preferences.manifest import PreferencesManifest
    from exopy.app.dependencies.manifest import DependenciesManifest
    from exopy.app.icons.manifest import IconManagerManifest
    from exopy.app.errors.manifest import ErrorsManifest
    from exopy.app.states.manifest import StateManifest
    from exopy.app.errors.plugin import ErrorsPlugin
    from exopy.instruments.manifest import InstrumentManagerManifest


pytests_plugin = str('exopy.testing.fixtures'),


@pytest.fixture
def instr_workbench(workbench, monkeypatch, app_dir, app):
    """Setup the workbench in such a way that the instrs manager can be tested.

    """
    monkeypatch.setattr(ErrorsPlugin, 'exit_error_gathering', exit_on_err)
    workbench.register(CoreManifest())
    workbench.register(AppManifest())
    workbench.register(PreferencesManifest())
    workbench.register(IconManagerManifest())
    workbench.register(ErrorsManifest())
    workbench.register(StateManifest())
    workbench.register(DependenciesManifest())
    workbench.register(InstrumentManagerManifest())

    yield workbench

    for m_id in ('exopy.instruments', 'exopy.app.dependencies',
                 'exopy.app.errors', 'exopy.app.preferences',
                 'exopy.app.icons', 'exopy.app.states', 'exopy.app'):
        try:
            workbench.unregister(m_id)
        except Exception:
            pass

        # Give some time to the os to release resources linked to file
        # monitoring.
        sleep(0.1)
