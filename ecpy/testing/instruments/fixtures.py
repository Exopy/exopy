# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Fixture for testing the instruments manager plugin.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
from pprint import pformat

import enaml

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest

    from ecpy.app.app_manifest import AppManifest
    from ecpy.app.preferences.manifest import PreferencesManifest
    from ecpy.app.dependencies.manifest import DependenciesManifest
    from ecpy.app.icons.manifest import IconManagerManifest
    from ecpy.app.errors.manifest import ErrorsManifest
    from ecpy.app.states.manifest import StateManifest
    from ecpy.app.errors.plugin import ErrorsPlugin
    from ecpy.instruments.manifest import InstrumentManagerManifest


pytests_plugin = str('ecpy.testing.fixtures'),


@pytest.yield_fixture
def instr_workbench(workbench, monkeypatch, app_dir, app):
    """Setup the workbench in such a way that the instrs manager can be tested.

    """
    def exit_err(self):
        """Turn error reporting into error raising.

        """
        if self._delayed:
            raise Exception('Unexpected exceptions occured :\n' +
                            pformat(self._delayed))

    monkeypatch.setattr(ErrorsPlugin, 'exit_error_gathering', exit_err)
    workbench.register(CoreManifest())
    workbench.register(AppManifest())
    workbench.register(PreferencesManifest())
    workbench.register(IconManagerManifest())
    workbench.register(ErrorsManifest())
    workbench.register(StateManifest())
    workbench.register(DependenciesManifest())
    workbench.register(InstrumentManagerManifest())

    yield workbench

    for m_id in ('ecpy.instruments', 'ecpy.app.dependencies',
                 'ecpy.app.errors', 'ecpy.app.preferences',
                 'ecpy.app.icons', 'ecpy.app.states', 'ecpy.app'):
        try:
            workbench.unregister(m_id)
        except Exception:
            pass
