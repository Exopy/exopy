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

from future.builtins import str


def collect_task(workbench, obj, getter, dependencies, errors):
    """Collector function working on tasks and saved task representation.

    """
    # Here we use direct call to plugin methods as this is internal to the
    # plugin
    manager = workbench.get_plugin('ecpy.tasks')

    t_cls_name = getter(obj, 'task_class')
    t_infos = manager.get_task_infos(t_cls_name)

    if t_infos is None:
        errors[t_cls_name] = 'Unknown task.'
        return

    dependencies[t_cls_name] = t_infos.cls

    return t_infos.dependencies


def collect_interface(workbench, obj, getter, dependencies, errors):
    """Collector function working on interfaces and saved interfaces.

    """
    # Here we use direct call to plugin methods as this is internal to the
    # plugin
    manager = workbench.get_plugin('ecpy.tasks')

    interface_anchor = getter(obj, 'interface_class')
    if not isinstance(interface_anchor, tuple):
        interface_anchor = literal_eval(interface_anchor)

    i_infos = manager.get_interface_infos(interface_anchor)

    if i_infos is None:
        msg = 'Unknown interface.'
        errors[str(interface_anchor)] = msg
        return

    dependencies[interface_anchor] = i_infos.cls

    return i_infos.dependencies
