# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the shared ressources.

Given how messy it is to properly test thread-safety I don't try and just
check that in single thread things work.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from exopy.tasks.tasks.shared_resources import SharedCounter, SharedDict


def test_shared_counter():
    """Test the shared counter.

    """
    counter = SharedCounter()

    assert counter.count == 0
    counter.increment()
    assert counter.count == 1
    counter.decrement()
    assert counter.count == 0


def test_shared_dict():
    """Test the shared dict implementation.

    """
    sdict = SharedDict()
    sdict = SharedDict(set)
    with sdict.safe_access('test') as v:
        assert v == set()
        v.add(1)

    with sdict.locked():
        assert sdict['test'] == set([1])
        assert sdict.get('test2') is None

    assert len(sdict) == 1
    sdict['test2'] = set([2])
    assert sdict['test2'] == set([2])
    del sdict['test2']
    assert sdict['test2'] == set()
    assert 'test' in sdict

    for i in sdict:
        pass
