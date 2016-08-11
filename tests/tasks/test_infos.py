# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test of the functionality of task, interface and config infos.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from ecpy.tasks.infos import ObjectDependentInfos, TaskInfos


def test_dependencies_handling():
    """Check that dependencies are correctly updated when instruments are.

    """
    infos = TaskInfos(dependencies=['test'])

    infos.instruments = ['e']

    assert len(infos.dependencies) == 3

    infos.instruments.update(['t', 'y'])

    assert len(infos.dependencies) == 3

    infos.instruments = []

    assert set(['test']) == infos.dependencies


def test_interfaces_walking():
    """Check that interfaces walking does yield interfaces and respect depth.

    """
    ints = {'interface1':
            ObjectDependentInfos(interfaces={'i': ObjectDependentInfos()}),
            'interface2': ObjectDependentInfos()}
    infos = ObjectDependentInfos(interfaces=ints)
    print(list(zip(*infos.walk_interfaces())))
    assert (sorted(list(zip(*infos.walk_interfaces()))[0]) ==
            sorted(('interface1', 'i', 'interface2')))

    assert (sorted(list(zip(*infos.walk_interfaces(0)))[0]) ==
            sorted(('interface1', 'interface2')))
