# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the mapping utilities functions.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from ecpy.utils.mapping_utils import recursive_update


def test_recurvise_update():
    a = {'a': {'a1': 1}}
    b = {'b': True}
    c = {'a': {'a1': 2, 'c': 1}}

    recursive_update(a, b)
    assert a == {'a': {'a1': 1}, 'b': True}

    recursive_update(a, c)
    assert a == {'a': {'a1': 2, 'c': 1}, 'b': True}


def test_recurvise_update2():
    a = {}
    b = {'b': True}
    c = {'a': {'a1': 2, 'c': 1}}

    recursive_update(a, b)
    assert a == {'b': True}

    recursive_update(a, c)
    assert a == {'a': {'a1': 2, 'c': 1}, 'b': True}
