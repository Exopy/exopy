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
import sys
import os
import gc
import weakref
import inspect
from contextlib import contextmanager
from pprint import pformat

import enaml
from configobj import ConfigObj
from atom.api import Atom, Bool
from enaml.application import timed_call
from enaml.widgets.api import Window, Dialog, PopupView
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


def run_pending_tasks(qtbot, timeout=1000):
    """Run all enaml pending tasks.

    WARNING: this may not run the Qt event loop if no task is pending.
    This will only deal with tasks schedule through the schedule function
    (or Application method)

    Parameters
    ----------
    timeout : int, optional
        Timeout after which the operation should fail in ms

    """
    def check_pending_tasks():
        assert not qtbot.enaml_app.has_pending_tasks()
    qtbot.wait_until(check_pending_tasks)


def get_window(qtbot, cls=Window, timeout=1000):
    """Convenience function running the event loop and returning the first
    window found in the set of active windows.

    Parameters
    ----------
    cls : type, optional
        Type of the window which should be returned.

    timeout : int, optional
        Timeout after which the operation should fail in ms

    Returns
    -------
    window : Window or None
        Return the first window found matching the specified class

    Raises
    ------
    AssertionError : raised if no window is found in the given time

    """
    def check_window_presence():
        print(Window.windows)
        assert [w for w in Window.windows if isinstance(w, cls)]

    qtbot.wait_until(check_window_presence)
    for w in Window.windows:
        if isinstance(w, cls):
            return w


def get_popup(qtbot, cls=PopupView, timeout=1000):
    """Convenience function running the event loop and returning the first
    popup found in the set of active popups.

    Parameters
    ----------
    cls : type, optional
        Type of the window which should be returned.

    timeout : int, optional
        Timeout after which the operation should fail in ms

    Returns
    -------
    popup : PopupView or None
        Return the first window found matching the specified class

    Raises
    ------
    AssertionError : raised if no popup is found in the given time

    """
    def check_popup_presence():
        assert [p for p in PopupView.popup_views if isinstance(p, cls)]

    qtbot.wait_until(check_popup_presence)
    for p in PopupView.popup_views:
        if isinstance(p, cls):
            return p


def wait_for_window_displayed(qtbot, window, timeout=1000):
    """Wait for a window to be displayed.

    This method should be called on already activated windows (the show method
    should have been called).

    """
    if not window.proxy_is_active or not window.proxy.widget:
        msg = 'Window must be activated before waiting for display'
        raise RuntimeError(msg)
    qtbot.wait_for_window_shown(window.proxy.widget)


class EventObserver(Atom):
    """Simple observer registering the fact it was called once.

    """
    called = Bool()

    def callback(self, change):
        self.called = True

    def assert_called(self):
        assert self.called


def wait_for_destruction(qtbot, widget):
    """Wait for a widget to get destroyed.

    """
    if widget.is_destroyed:
        return
    obs = EventObserver()
    widget.observe('destroyed', obs.callback)
    qtbot.wait_until(obs.assert_called)


def close_window_or_popup(qtbot, window_or_popup):
    """Close a window/popup and run the event loop to make sure the closing
    complete.

    """
    if window_or_popup.is_destroyed:
        return
    obs = EventObserver()
    window_or_popup.observe('destroyed', obs.callback)
    window_or_popup.close()
    qtbot.wait_until(obs.assert_called)


@contextmanager
def close_all_windows(qtbot):
    """Close all opened windows.

    """
    yield
    run_pending_tasks(qtbot)
    while Window.windows:
        windows = list(Window.windows)
        # First close non top level windows to avoid a window to lose its
        # parent and not remove itself from the set of windows.
        non_top_level_windows = [w for w in windows if w.parent is not None]
        for window in non_top_level_windows:
            close_window_or_popup(qtbot, window)
        for window in windows:
            close_window_or_popup(qtbot, window)


@contextmanager
def close_all_popups(qtbot):
    """Close all opened popups.

    """
    yield
    run_pending_tasks(qtbot)
    while PopupView.popup_views:
        popups = list(PopupView.popup_views)
        # First close non top level popups to avoid a up/window to lose its
        # parent and not remove itself from the set of windows.
        non_top_level_popups = [p for p in popups if p.parent is not None]
        for popup in non_top_level_popups:
            close_window_or_popup(qtbot, popup)
        for popup in popups:
            close_window_or_popup(qtbot, popup)


class ScheduledClosing(object):
    """Scheduled closing of dialog.

    """

    def __init__(self, bot, cls, handler, op, skip_answer):
        self.cls = cls
        self.handler = handler
        self.op = op
        self.bot = bot
        self.skip_answer = skip_answer
        self.called = False

    def __call__(self):
        self.called = True
        from .fixtures import dialog_sleep
        dial = get_window(self.bot, cls=self.cls)
        wait_for_window_displayed(self.bot, dial)
        self.bot.wait(dialog_sleep())
        obs = EventObserver()
        dial.observe('finished', obs.callback)

        try:
            self.handler(self.bot, dial)
        finally:
            if not self.skip_answer:
                getattr(dial, self.op)()

            self.bot.wait_until(obs.assert_called, timeout=10e3)

    def was_called(self):
        """Assert the scheduler was called.

        """
        assert self.called


@contextmanager
def handle_dialog(qtbot, op='accept', handler=lambda qtbot, window: window,
                  cls=Dialog, time=100, skip_answer=False):
    """Automatically close a dialog opened during the context.

    Parameters
    ----------
    op : {'accept', 'reject'}, optional
        Whether to accept or reject the dialog.

    handler : callable, optional
        Callable taking as arguments the bot and the dialog, called before
        accepting or rejecting the dialog.

    cls : type, optional
        Dialog class to identify.

    time : float, optional
        Time to wait before handling the dialog in ms.

    skip_answer : bool, optional
        Skip answering to the dialog. If this is True the handler should handle
        the answer itself.

    """
    sch = ScheduledClosing(qtbot, cls, handler, op, skip_answer)
    timed_call(time, sch)
    try:
        yield
    except Exception:
        raise
    else:
        qtbot.wait_until(sch.was_called, 10e3)


@contextmanager
def handle_question(qtbot, answer):
    """Handle question dialog.

    """
    def answer_question(qtbot, dial):
        """Mark the right button as clicked.

        """
        dial.buttons[0 if answer == 'yes' else 1].was_clicked = True

    with handle_dialog(qtbot, 'accept' if answer == 'yes' else 'reject',
                       handler=answer_question, cls=MessageBox):
        yield


def show_widget(qtbot, widget):
    """Show a widget in a window

    """
    win = Window()
    win.insert_children(None, [widget])
    win.show()
    wait_for_window_displayed(qtbot, win)
    return win


def show_and_close_widget(qtbot, widget):
    """Show a widget in a window and then close it.

    """
    from .fixtures import DIALOG_SLEEP
    win = show_widget(qtbot, widget)
    qtbot.wait(DIALOG_SLEEP)
    close_window_or_popup(qtbot, win)


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
