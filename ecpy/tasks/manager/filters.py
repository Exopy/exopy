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

from atom.api import Value, Subclass, Unicode, Property, set_default
from enaml.core.api import d_func, d_

from ..base_tasks import BaseTask
from ...utils.declarator import Declarator


class TaskFilter(Declarator):
    """Base class for all task filters.

    """
    #: Unique id of this filter (also used as a name).
    id = d_(Unicode())

    @d_func
    def filter_tasks(self, tasks, templates):
        """Filter the task known by the manager.

        By default all task are returned.

        Parameters
        ----------
        tasks : dict
            Dictionary of known python tasks as name : TaskInfos.

        templates : dict
            Dictionary of known templates as name : path

        Returns
        -------
        task_names : list(str)
            List of the name of the task matching the filters criteria.

        """
        return list(tasks) + list(templates)


class SubclassTaskFilter(TaskFilter):
    """Filter keeping only the python tasks which are subclass of subclass.

    """
    #: Class from which the task must inherit.
    subclass = d_(Subclass(BaseTask))

    @d_func
    def filter_tasks(self, tasks, templates):
        """Keep only the task inheriting from the right class.

        """
        return [name for name, infos in tasks.items()
                if issubclass(infos.cls, self.subclass)]


class MetadataTaskFilter(TaskFilter):
    """Filter keeping only the python tasks with the right class attribute.

    """
    #: Metadata key to match.
    meta_key = d_(Unicode())

    #: Metadata value to match.
    meta_value = d_(Value())

    @d_func
    def filter_tasks(self, tasks, templates):
        """Keep only the task with the right class attribute.

        """
        tasks = [name for name, infos in tasks.items()
                 if infos.metadata.get(self.meta_key) == self.meta_value]

        return tasks


class GroupTaskFilter(MetadataTaskFilter):
    """Filter keeping only the python tasks from the right group.

    """
    #: Group to which the tasks must belong.
    group = d_(Unicode())

    meta_key = set_default('group')

    meta_value = Property()

    def _get_meta_value(self):
        return self.group
