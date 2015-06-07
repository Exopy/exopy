# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Utility function to collect task and interfaces dependencies.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from ast import literal_eval


def collect_tasks_and_interfaces(workbench, flat_walk):
    """Collector function for the build-dependencies extensions.

    """
    # Here we use direct call to plugin methods as this is internal to the
    # plugin
    manager = workbench.get_plugin('ecpy.tasks.manager')

    t_res = manager.get_tasks(flat_walk['task_class'])

    interfaces = list(flat_walk['interface_class'])
    if interfaces and not isinstance(interfaces[0], tuple):
        interfaces = [literal_eval(ic) for ic in interfaces]
    i_res = manager.interfaces_request(interfaces)

    if t_res[1] or i_res[1]:
        mess = 'Missing tasks: {}, missing interfaces: {}'.format(t_res[1],
                                                                  i_res[1])
        raise ValueError(mess)

    dependencies = {}
    if flat_walk['task_class']:
        dependencies['tasks'] = t_res[0]
    if flat_walk['interface_class']:
        dependencies['interfaces'] = i_res[0]

    return dependencies
