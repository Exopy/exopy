# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Generic utility functions for testing.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import sys
import os
import gc
import weakref
import inspect
from time import sleep
from contextlib import contextmanager
from pprint import pformat

import enaml
from configobj import ConfigObj
from enaml.application import timed_call
from enaml.qt.qt_application import QtApplication
from enaml.widgets.api import Window, Dialog
with enaml.imports():
    from enaml.stdlib.message_box import MessageBox

APP_PREFERENCES = os.path.join('app', 'preferences')
APP_DIR_CONFIG = 'app_directory.ini'


def exopy_path():
    """Get the exopy path as determined by the sys_path fixture.

    """
    from .fixtures import EXOPY
    assert EXOPY
    return EXOPY


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


class ScheduledClosing(object):
    """Scheduled closing of dialog.

    """

    def __init__(self, cls, handler, op, skip_answer):
        self.called = False
        self.cls = cls
        self.handler = handler
        self.op = op
        self.skip_answer = skip_answer

    def __call__(self):
        i = 0
        while True:
            dial = get_window(self.cls)
            if dial is not None:
                break
            elif i > 10:
                raise Exception('Dialog timeout')
            sleep(0.1)
            i += 1

        try:
            self.handler(dial)
        finally:
            process_app_events()
            from .fixtures import DIALOG_SLEEP
            sleep(DIALOG_SLEEP)
            if not self.skip_answer:
                getattr(dial, self.op)()
            self.called = True


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
    sch = ScheduledClosing(cls, custom, op, skip_answer)
    timed_call(time, sch)
    try:
        yield
    except Exception:
        raise
    else:
        while not sch.called:
            process_app_events()


@contextmanager
def handle_question(answer):
    """Handle question dialog.

    """
    def answer_question(dial):
        """Mark the right button as clicked.

        """
        dial.buttons[0 if answer == 'yes' else 1].was_clicked = True

    with handle_dialog('accept' if answer == 'yes' else 'reject',
                       custom=answer_question, cls=MessageBox):
        yield


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
    plugin = workbench.get_plugin('exopy.app.preferences')
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
    from exopy.app.errors.plugin import ErrorsPlugin
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


def exit_on_err(self):
    """Replacement function for exopy.app.errors plugin exit_error_gathering.

    This function will raise instead of displaying a dialog. Useful to catch
    unexpected errors.

    Should be used in conjunction with the monkeypatch fixture.

    """
    self._gathering_counter -= 1
    if self._gathering_counter < 1:
        self._gathering_counter = 0
        if self._delayed:
            msg = 'Unexpected exceptions occured :\n'
            raise ErrorDialogException(msg + pformat(self._delayed))


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


class ObjectTracker(object):
    """Object tracking instance of a given class exists.

    It works by patching __new__ and keeping a WeakSet of the created objects.
    So instances created before creating the tracker are not tracked.

    If the objects are not weak referenceable you should set has_weakref to
    False. By default objects inheriting from Atom are not weak referenceable.
    It provides way to list the object referring alive objects to help tracking
    ref leaks.

    """
    def __init__(self, cls, has_weakref=True):
        self._refs = weakref.WeakSet()

        # Create a weak referenceable subclass if necessary
        if not has_weakref:
            class __weakref_cls__(cls):
                __slots__ = ('__weakref__',)
        else:
            __weakref_cls__ = cls

        def override_new(original_cls, *args, **kwargs):
            """Function replacing new allowing to track instances.

            """
            new = __weakref_cls__.__old_new__(__weakref_cls__, *args, **kwargs)
            self._refs.add(new)
            return new

        __weakref_cls__.__old_new__ = cls.__new__
        cls.__new__ = (override_new if sys.version_info >= (3,) else
                       staticmethod(override_new))
        __weakref_cls__.original_cls = cls

        self.cls = __weakref_cls__

    def stop_tracking(self):
        """Use to properly remove tracking.

        """
        self.cls.original_cls.__new__ = self.cls.__old_new__

    @property
    def alive_instances(self):
        """Currently alive instances of the tracked objects.

        """
        gc.collect()
        return self._refs

    def list_referrers(self, exclude=[], depth=0):
        """List all the referrers of the tracked objects.

        Can exlude some objects and go to deeper levels (referrers of the
        referrers) in which case reference to the first object are filtered.
        References held by frames are also filtered

        This function is mostly useful when tracking why an object that is
        expected to be released is not.

        """
        gc.collect()

        def find_referrers(ref_dict, obj, depth=0, exclude=[]):
            """Find the object referring the specified object.

            """
            referrers = [ref for ref in gc.get_referrers(obj)
                         if not (inspect.isframe(ref) or
                         ref in exclude)]
            if depth == 0:
                ref_dict[obj] = referrers
            else:
                deeper = {}
                for r in referrers:
                    find_referrers(deeper, r, depth-1,
                                   exclude + [obj, referrers])
                ref_dict[obj] = deeper

        tracked = {}
        objs = [r for r in self._refs if r not in exclude]
        for r in objs:
            find_referrers(tracked, r, depth, [objs])

        return tracked
