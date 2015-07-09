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
from contextlib import contextmanager

from enaml.application import deferred_call
from enaml.qt.qt_application import QtApplication
from enaml.widgets.api import Window, Dialog


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
    while qapp.hasPendingEvents():
        qapp.processEvents()
        qapp.flush()


def get_window(cls=Window):
    """Convenience function running the event loop and returning the first
    window found in the set of active windows.

    Parameters
    ----------
    cls : type, optional
        Type of the window which should be returned.

    Raises
    ------
    UnboundLocalError : if no window exists.

    """
    process_app_events()
    sleep(0.1)
    for w in Window.windows:
        if isinstance(w, cls):
            w_ = w
            break

    return w_


def close_all_windows():
    """Close all opened windows.

    This should be used by all tests creating windows in a teardown step.

    """
    process_app_events()
    sleep(0.1)
    for window in Window.windows:
        window.close()
    process_app_events()


@contextmanager
def handle_dialog(op='accept', custom=lambda x: x, cls=Dialog):
    """Automatically close a dialog opened during the context.

    Parameters
    ----------
    op : {'accept', 'reject'}, optional
        Whether to accept or reject the dialog.

    custom : callable, optional
        Callable taking as only argument the dialog, called before accepting
        or rejecting the dialog.

    cls : type, optional


    """
    def close_dialog():
        dial = get_window(cls)
        try:
            custom(dial)
        finally:
            process_app_events()
            from .conftest import DIALOG_SLEEP
            sleep(DIALOG_SLEEP)
            getattr(dial, op)()
    deferred_call(close_dialog)
    yield
    process_app_events()


def show_widget(widget):
    """Show a widget in a window

    """
    win = Window()
    win.insert_children(None, [widget])
    win.show()
    process_app_events()
    return win


def show_and_close_widget(widget):
    """Show a widget in a window and then close it.

    """
    from .conftest import DIALOG_SLEEP
    try:
        win = show_widget(widget)
        sleep(DIALOG_SLEEP)
        win.close()
        process_app_events()
    except Exception:
        close_all_windows()
        raise
