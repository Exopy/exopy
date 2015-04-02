# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the walks utility functions.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from ecpy.utils.walks import flatten_walk


def test_flatten_walk():

    walk = [{'test1': 2, 'test2': 5},
            [{'test1': 2}, {'test3': 5},
             [{'test3': 6}]
             ]
            ]
    flat = flatten_walk(walk, ('test1', 'test3'))
    assert flat == {'test1': set((2,)), 'test3': set((5, 6))}
