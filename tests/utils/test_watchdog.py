# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the watchdog utilities.

"""
import pytest

from watchdog.events import FileCreatedEvent, FileDeletedEvent, FileMovedEvent

from exopy.utils.watchdog import SystematicFileUpdater


@pytest.fixture
def updater():

    class Tester(SystematicFileUpdater):

        def __init__(self):
            self.counter = 0
            super(Tester, self).__init__(lambda: setattr(self, 'counter',
                                                         self.counter + 1))

    return Tester()


def test_file_creation(updater):

    updater.on_created(FileCreatedEvent(''))
    assert updater.counter == 1


def test_file_deletion(updater):

    updater.on_deleted(FileDeletedEvent(''))
    assert updater.counter == 1


def test_file_moved(updater):

    updater.on_moved(FileMovedEvent('', ''))
    assert updater.counter == 1
