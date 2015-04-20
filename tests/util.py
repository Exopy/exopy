# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Generic utility functions for testing.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os
from time import sleep
from enaml.qt.qt_application import QtApplication
from enaml.widgets.api import Window


APP_PREFERENCES = os.path.join('app', 'preferences')
APP_DIR_CONFIG = 'app_directory.ini'


def ecpy_path():
    """Get the ecpy path as determined by the sys_path fixture.

    """
    from .conftest import ECPY
    assert ECPY
    return ECPY


def process_app_events():
    """Manually run the Qt event loop so that windows are shown and event
    propagated.

    """
    qapp = QtApplication.instance()._qapp
    qapp.flush()
    qapp.processEvents()


def get_window():
    """Convenience function running the event loop and returning the first
    window found in the set of active windows.

    """
    process_app_events()
    sleep(0.1)
    for w in Window.windows:
        break

    return w


def close_all_windows():
    """Close all opened windows.

    This should be used by all tests creating windows in a teardown step.

    """
    process_app_events()
    sleep(0.1)
    for window in Window.windows:
        window.close()
    process_app_events()
