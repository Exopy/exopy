# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Configuartion of the test of the icon manager plugin.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
import enaml

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from ecpy.app.preferences.manifest import PreferencesManifest
    from ecpy.app.icons.manifest import IconManagerManifest


@pytest.yield_fixture
def icon_workbench(workbench, app_dir):
    """Register the icon mannager plugin and dependencies.

    """
    workbench.register(CoreManifest())
    workbench.register(PreferencesManifest())
    workbench.register(IconManagerManifest())

    yield workbench

    for m_id in ('ecpy.app.icons', 'ecpy.app.preferences'):
        try:
            workbench.unregister(m_id)
        except Exception:
            pass
