# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the BitFlag object.

The thread safety is ensured by the lock and is not explicitely tested.

"""
from threading import Thread
from time import sleep

import pytest

from exopy.utils.flags import BitFlag


@pytest.fixture
def flag():
    """Fixture creating a flag.

    """
    return BitFlag(('start', 'stop'))


def test_flag_test(flag):
    """Test the verification of the flag value.

    """
    flag._state = 1
    assert flag.test('start')
    assert not flag.test('start', 'stop')


def test_flag_set(flag):
    """Test setting the flag.

    """
    flag.set('stop')
    assert not flag.test('start')
    assert flag.test('stop')

    flag.set('start', 'stop')
    assert flag.test('start', 'stop')


def test_flag_clear(flag):
    """Test cleraing values from the flag.

    """
    flag.set('start', 'stop')
    flag.clear('start')
    assert not flag.test('start')
    assert flag.test('stop')

    flag.clear()
    assert not flag.test('stop')


@pytest.mark.timeout(1)
def test_flag_wait(flag):
    """Test asking a thread to wait on a flag.

    """
    def wait(flag):
        flag.wait(0.01, 'start', 'stop')

    thread = Thread(target=wait, args=(flag,))
    thread.start()

    flag.set('start')
    sleep(0.02)
    flag.set('stop')
    sleep(0.02)

    thread.join()
