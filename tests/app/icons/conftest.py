# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Configuartion of the test of the icon manager plugin.

"""
import pytest
import enaml

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from exopy.app.preferences.manifest import PreferencesManifest
    from exopy.app.icons.manifest import IconManagerManifest


@pytest.yield_fixture
def icon_workbench(workbench, app_dir):
    """Register the icon mannager plugin and dependencies.

    """
    workbench.register(CoreManifest())
    workbench.register(PreferencesManifest())
    workbench.register(IconManagerManifest())

    yield workbench

    for m_id in ('exopy.app.icons', 'exopy.app.preferences'):
        try:
            workbench.unregister(m_id)
        except Exception:
            pass
