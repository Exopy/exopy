# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the capabilities of the container for the measurement.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
from atom.api import List

from exopy.measurement.container import MeasurementContainer


@pytest.fixture
def container():
    class ObservedContainer(MeasurementContainer):

        changes = List()

    cont = ObservedContainer()
    cont.observe('changed', lambda c: c.obj.changes.append(c))
    return cont


def test_add(container):
    """Test adding a new object in the container.

    """
    obj = object()
    container.add(obj)
    assert len(container.changes) == 1
    assert container.changes[0].added
    assert not container.changes[0].removed
    assert not container.changes[0].moved
    assert not container.changes[0].collapsed

    obj2 = object()
    container.add(obj2, 0)
    assert container.measurements[0] is obj2


def test_move(container):
    """Test moving a measurement.

    """
    obj1 = object()
    obj2 = object()
    obj3 = object()
    container.measurements = [obj1, obj2, obj3]
    container.move(1, 2)
    assert container.measurements == [obj1, obj3, obj2]
    assert container.changes[0].moved
    assert not container.changes[0].added
    assert not container.changes[0].removed
    assert not container.changes[0].collapsed


def test_remove(container):
    """Test removing a measurement.

    """
    obj1 = object()
    obj2 = object()
    obj3 = object()
    container.measurements = [obj1, obj2, obj3]
    container.remove(obj2)
    assert container.measurements == [obj1, obj3]
    assert container.changes[0].removed
    assert not container.changes[0].added
    assert not container.changes[0].moved
    assert not container.changes[0].collapsed
