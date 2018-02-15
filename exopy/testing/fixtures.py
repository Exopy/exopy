# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Pytest fixtures.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os
from os import remove  # Avoid issue when monkeypatching it
import logging
from inspect import getabsfile

import pytest
from configobj import ConfigObj
from future.builtins import str as text
from enaml.qt.qt_application import QtApplication
from enaml.workbench.api import Workbench


from .util import (APP_DIR_CONFIG, APP_PREFERENCES, close_all_windows,
                   close_all_popups, exopy_path)

#: Global variable storing the application folder path
EXOPY = ''


#: Global variable linked to the --exopy-sleep cmd line option.
DIALOG_SLEEP = 0


def pytest_addoption(parser):
    """Add command line options.

    """
    parser.addoption("--exopy-sleep", action='store', type=float,
                     help="Time to sleep after showing a dialog")


def pytest_configure(config):
    """Turn the --exopy-sleep command line into a global variable.

    """
    s = config.getoption('--exopy-sleep')
    if s is not None:
        global DIALOG_SLEEP
        DIALOG_SLEEP = s*1000


@pytest.fixture
def dialog_sleep():
    """Return the time to sleep as set by the --exopy-sleep option.

    """
    return DIALOG_SLEEP


@pytest.yield_fixture(scope='session', autouse=True)
def sys_path():
    """Detect installation path of exopy.

    Automtically called, DOES NOT use directly. Use exopy_path to get the path
    to the exopy directory.

    """
    import exopy

    # Hiding current app_directory.ini to avoid losing user choice.
    path = os.path.dirname(getabsfile(exopy))
    pref_path = os.path.join(path, APP_PREFERENCES)
    app_dir = os.path.join(pref_path, APP_DIR_CONFIG)
    new = os.path.join(pref_path, '_' + APP_DIR_CONFIG)

    # If a hidden file exists already assume it is because previous test
    # failed and do nothing.
    if os.path.isfile(app_dir) and not os.path.isfile(new):
        os.rename(app_dir, new)

    global EXOPY
    EXOPY = path

    yield

    # Remove created app_directory.ini and put hold one back in place.
    app_dir = os.path.join(pref_path, APP_DIR_CONFIG)
    if os.path.isfile(app_dir):
        os.remove(app_dir)

    # Put user file back in place.
    protected = os.path.join(pref_path, '_' + APP_DIR_CONFIG)
    if os.path.isfile(protected):
        os.rename(protected, app_dir)


@pytest.fixture(scope='session', autouse=True)
def watchdog_on_travis():
    """Do not use inotify on travis as it tends to break builds.

    """
    if 'TRAVIS' in os.environ:
        print('Using polling observer on Travis')
        from watchdog.observers.polling import PollingObserver
        import watchdog.observers
        watchdog.observers.Observer = PollingObserver


@pytest.yield_fixture(scope='session')
def app():
    """Make sure a QtApplication is active.

    """
    app = QtApplication.instance()
    if app is None:
        app = QtApplication()
        yield app
        app.stop()
    else:
        yield app


@pytest.yield_fixture
def exopy_qtbot(app, qtbot):
    qtbot.enaml_app = app
    with close_all_windows(qtbot), close_all_popups(qtbot):
        yield qtbot


@pytest.yield_fixture
def app_dir(tmpdir):
    """Fixture setting the app_directory.ini file for each test.

    """
    # Create a trash app_directory.ini file. The global fixture ensure
    # that it cannot be a user file.
    app_pref = os.path.join(exopy_path(), APP_PREFERENCES, APP_DIR_CONFIG)
    app_dir = text(tmpdir)
    conf = ConfigObj(encoding='utf-8', indent_type='    ')
    conf.filename = app_pref
    conf['app_path'] = app_dir
    conf.write()
    yield app_dir
    remove(app_pref)


@pytest.yield_fixture
def logger(caplog):
    """Fixture returning a logger for testing and cleaning handlers afterwards.

    """
    logger = logging.getLogger('test')

    yield logger

    logger.handlers = []


@pytest.fixture
def workbench():
    """Create a workbench instance.

    """
    workbench = Workbench()
    return workbench
