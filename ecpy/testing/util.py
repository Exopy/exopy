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

from configobj import ConfigObj
from enaml.application import timed_call
from enaml.qt.qt_application import QtApplication
from enaml.widgets.api import Window, Dialog


APP_PREFERENCES = os.path.join('app', 'preferences')
APP_DIR_CONFIG = 'app_directory.ini'


def ecpy_path():
    """Get the ecpy path as determined by the sys_path fixture.

    """
    from .fixtures import ECPY
    assert ECPY
    return ECPY


def process_app_events():
    """Manually run the Qt event loop so that windows are shown and event
    propagated.

    """
    qapp = QtApplication.instance()._qapp
    qapp.flush()
    qapp.processEvents()
    qapp.sendPostedEvents()


def get_window(cls=Window):
    """Convenience function running the event loop and returning the first
    window found in the set of active windows.

    Parameters
    ----------
    cls : type, optional
        Type of the window which should be returned.

    """
    sleep(0.1)
    process_app_events()
    w_ = None
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
    while Window.windows:
        for window in list(Window.windows):
            window.close()
        process_app_events()
        sleep(0.02)


@contextmanager
def handle_dialog(op='accept', custom=lambda x: x, cls=Dialog, time=100,
                  skip_answer=False):
    """Automatically close a dialog opened during the context.

    Parameters
    ----------
    op : {'accept', 'reject'}, optional
        Whether to accept or reject the dialog.

    custom : callable, optional
        Callable taking as only argument the dialog, called before accepting
        or rejecting the dialog.

    cls : type, optional
        Dialog class to identify.

    time : float, optional
        Time to wait before handling the dialog in ms.

    skip_answer : bool, optional
        Skip answering to the dialog. If this is True the handler should handle
        the answer itself.

    """
    def close_dialog():
        i = 0
        while True:
            dial = get_window(cls)
            if dial is not None:
                break
            elif i > 10:
                raise Exception('Dialog timeout')
            sleep(0.1)
            i += 1

        try:
            custom(dial)
        finally:
            process_app_events()
            from .fixtures import DIALOG_SLEEP
            sleep(DIALOG_SLEEP)
            getattr(dial, op)()
    timed_call(time, close_dialog)
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
    from .fixtures import DIALOG_SLEEP
    win = show_widget(widget)
    sleep(DIALOG_SLEEP)
    win.close()
    process_app_events()

    close_all_windows()


def set_preferences(workbench, preferences):
    """Set the preferences stored in the preference plugin.

    This function must be called before accessing any plugin relying on those
    values.

    Parameters
    ----------
    workbench :
        Application workbench.

    preferences : dict
        Dictionary describing the preferences.

    """
    plugin = workbench.get_plugin('ecpy.app.preferences')
    plugin._prefs = ConfigObj(preferences, indent_type='    ',
                              encoding='utf-8')


class ErrorDialogException(Exception):
    """Error raised when patching the error plugin to raise rather than show a
    dialog when exiting error gathering.

    """
    pass


@contextmanager
def signal_error_raise():
    """Make the error plugin raise an exception when signaling.

    """
    from ecpy.app.errors.plugin import ErrorsPlugin
    func = ErrorsPlugin.signal

    def raise_for_signal(self, kind, **kwargs):
        """Raise an easy to identify error.

        """
        raise ErrorDialogException()

    ErrorsPlugin.signal = raise_for_signal

    try:
        yield
    finally:
        ErrorsPlugin.signal = func


class CallSpy(object):
    """Object simply monitoring how many times it gets called.

    """
    __slots__ = ('called', 'args', 'kwargs')

    def __init__(self):
        self.called = 0

    def __call__(self, *args, **kwargs):
        self.called += 1
        self.args = args
        self.kwargs = kwargs
