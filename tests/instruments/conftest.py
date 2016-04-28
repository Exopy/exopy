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

import os
import shutil

import pytest
import enaml


with enaml.imports():
    from .contributors import InstrContributor1

pytest_plugins = str('ecpy.testing.instruments.fixtures'),

PROFILE_PATH = os.path.join(os.path.dirname(__file__),
                            'fp.instr.ini')


@pytest.fixture
def prof_plugin(app, instr_workbench):
    """Start the instrument plugin and add some profiles.

    """
    instr_workbench.register(InstrContributor1())
    p = instr_workbench.get_plugin('ecpy.instruments')
    # Test observation of profiles folders
    for n in ('fp1', 'fp2', 'fp3', 'fp4'):
        shutil.copyfile(PROFILE_PATH, os.path.join(p._profiles_folders[0],
                                                   n + '.instr.ini'))
    p._refresh_profiles()
    return p
