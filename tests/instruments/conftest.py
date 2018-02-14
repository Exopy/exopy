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
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os

import pytest
import enaml
from configobj import ConfigObj

with enaml.imports():
    from .contributors import InstrContributor1

from exopy.testing.instruments.util import add_profile

pytest_plugins = str('exopy.testing.instruments.fixtures'),

PROFILE_PATH = os.path.join(os.path.dirname(__file__),
                            'fp.instr.ini')


@pytest.fixture
def prof_plugin(app, instr_workbench):
    """Start the instrument plugin and add some profiles.

    """
    instr_workbench.register(InstrContributor1())
    c = ConfigObj(PROFILE_PATH, encoding='utf-8')
    add_profile(instr_workbench, c, ['fp1', 'fp2', 'fp3', 'fp4'])
    return instr_workbench.get_plugin('exopy.instruments')
