# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test operation on ConfigObj objects.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os
from configobj import ConfigObj

from ecpy.utils.configobj_ops import traverse_config, include_configobj


def test_include():

    a = ConfigObj()
    a['r'] = 2
    b = ConfigObj()
    b['a'] = {}
    b['a']['t'] = 3

    include_configobj(a, b)
    assert a == {'r': 2, 'a': {'t': 3}}


def test_traverse_configobj():
    """Test looking for specific keys in a ConfigObj object.

    """
    config = ConfigObj(os.path.join(os.path.dirname(__file__),
                       'config_test.ini'))

    ite = traverse_config(config)
    assert len(list(ite)) == 8

    assert len(list(traverse_config(config, 0))) == 4
