# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Modules defining the basic filters.

The filter available by default are declared in the manager manifest.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Subclass, Dict, Unicode
from enaml.core.api import d_func, d_

from ...base_tasks import BaseTask
from ....utils.declarator import Declarator
from ....utils.chainmap import ChainMap


class TaskFilter(Declarator):
    """Base class for all task filters.

    """

    @d_func
    def filter_tasks(self, py_tasks, template_tasks):
        """Filter the task known by the manager.

        By default all task are returned.

        Parameters
        ----------
        py_tasks : dict
            Dictionary of known python tasks stored by groups.

        template_tasks : dict
            Dictionary of known templates as name : path

        Returns
        -------
        task_names : list(str)
            List of the name of the task matching the filters criteria.

        """
        return list(ChainMap(*py_tasks.values())) + list(template_tasks.keys())


class SubclassTaskFilter(TaskFilter):
    """Filter keeping only the python tasks which are subclass of task_class.

    """

    #: Class from which the task must inherit.
    subclass = d_(Subclass(BaseTask))

    def filter_tasks(self, py_tasks, template_tasks):
        """Keep only the task inheriting from the right class.

        """
        return [name for name, decl in ChainMap(*py_tasks.values()).items()
                if issubclass(decl.task_cls, self.task_class)]


class GroupTaskFilter(TaskFilter):
    """Filter keeping only the python tasks from the right group.

    """
    #: Group to which the tasks must belong.
    group = d_(Unicode())

    @d_func
    def filter_tasks(self, py_tasks, template_tasks):
        """Keep only the task with the right class attribute.

        """
        return py_tasks[self.group].keys()


class ClassAttrTaskFilter(TaskFilter):
    """Filter keeping only the python tasks with the right class attribute.

    """

    class_attr = d_(Dict({'name': '', 'value': None}))

    @d_func
    def filter_tasks(self, py_tasks, template_tasks):
        """Keep only the task with the right class attribute.

        """
        attr_name = self.class_attr['name']
        attr_val = self.class_attr['value']
        tasks = [name for name, t_class in ChainMap(*py_tasks.values()).items()
                 if getattr(t_class, attr_name, None) == attr_val]

        return tasks
