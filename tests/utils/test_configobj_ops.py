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
import os
from configobj import ConfigObj
from nose.tools import assert_equal, assert_in

from ecpy.utils.configobj_ops import flatten_config, include_configobj


def test_include():

    a = ConfigObj()
    a['r'] = 2
    b = ConfigObj()
    b['a'] = {}
    b['a']['t'] = 3

    include_configobj(a, b)
    assert a == {'r': 2, 'a': {'t': 3}}


def test_flatten_configobj():
    """Test looking for specific keys in a ConfigObj object.

    """
    config = ConfigObj(os.path.join(os.path.dirname(__file__),
                       'config_test.ini'))

    flat = flatten_config(config, ['task_class', 'selected_profile'])
    assert_in('task_class', flat)
    assert_equal(flat['task_class'],
                 set(['ComplexTask', 'SaveTask', 'LoopTask',
                      'LockInMeasureTask', 'RFSourceSetFrequencyTask',
                      'FormulaTask']))

    assert_in('selected_profile', flat)
    assert_equal(flat['selected_profile'],
                 set(['Lock8', 'Lock12', 'RF19']))
