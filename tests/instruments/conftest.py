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
from time import sleep

import pytest
import enaml

with enaml.imports():
    from .contributors import InstrContributor1

pytest_plugins = str('ecpy.testing.instruments.fixtures'),

PROFILE_PATH = os.path.join(os.path.dirname(__file__),
                            'false_profile.instr.ini')


@pytest.fixture
def prof_plugin(instr_workbench):
    """Start the instrument plugin and add some profiles.

    """
    instr_workbench.register(InstrContributor1())
    p = instr_workbench.get_plugin('ecpy.instruments')
    # Test observation of profiles folders
    for n in ('fp1', 'fp2', 'fp3', 'fp4'):
        shutil.copyfile(PROFILE_PATH, os.path.join(p._profiles_folders[0],
                                                   n + '.instr.ini'))
    sleep(0.1)
    return p
