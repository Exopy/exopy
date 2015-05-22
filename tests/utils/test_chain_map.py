# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test of ReadOnlyChainMap.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)
import pytest

from ecpy.utils.chain_map import ReadOnlyChainMap


def test_chain_map():
    """Test ReadOnlyChainMap.

    """
    chain = ReadOnlyChainMap({'a': 1}, {'b': 2}, {1: 5})

    assert 'a' in chain
    assert len(chain) == 3
    assert bool(chain)
    assert sorted(chain) == sorted(['a', 'b', 1])
    assert chain[1] == 5
    assert chain.get('a') == 1
    assert chain.get(5) is None

    with pytest.raises(KeyError):
        chain[5]
