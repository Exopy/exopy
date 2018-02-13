# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Utility function used for testing instruments.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os


def add_profile(workbench, profile_config, names):
    """Add a profile to the instrument plugin.

    Parameters
    ----------
    workbench : Workbench
        Workbench of the application

    source_path : str
        Path to the source file for the profiles.

    names : list
        List of names under which the profiles should be added.

    """
    p = workbench.get_plugin('exopy.instruments')
    p._unbind_observers()
    # Test observation of profiles folders
    for n in names:
        with open(os.path.join(p._profiles_folders[0],  n + '.instr.ini'),
                  'wb') as f:
            profile_config.write(f)
    p._refresh_profiles()
    p._bind_observers()
