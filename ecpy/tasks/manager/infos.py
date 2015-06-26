# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Enaml objects used to declare tasks and interfaces in a plugin manifest.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Atom, List, Subclass, Dict, Coerced
import enaml

from ..base_tasks import BaseTask
from ..task_interface import BaseInterface

with enaml.imports():
    from ..base_views import BaseTaskView


INSTR_RUNTIME_ID = 'ecpy.instruments.runtime_deps'


class TaskDependentInfos(Atom):
    """Base infos for tasks and interfaces.

    """
    #: List of instrument supported by this task.
    instruments = Coerced(set, ())

    #: Build and runtime dependencies ids of this task.
    dependencies = Dict({'build': ['ecpy.tasks.build_deps'],
                         'runtime': []})

    def _post_setattr_dependencies(self, old, new):
        if new:
            if INSTR_RUNTIME_ID not in self.dependencies['runtime']:
                self.dependencies['runtime'].append(INSTR_RUNTIME_ID)
        elif INSTR_RUNTIME_ID in self.dependencies['runtime']:
            self.dependencies['runtime'].remove(INSTR_RUNTIME_ID)


class TaskInfos(TaskDependentInfos):
    """An object used to store informations about a task.

    """
    #: Class representing this task.
    cls = Subclass(BaseTask)

    #: Widget associated with this task.
    view = Subclass(BaseTaskView)

    #: List of interfaces supported by this task.
    interfaces = Dict()

    #: Metadata associated with this task such as group, looping capabilities,
    #: etc
    metadata = Dict()


class InterfaceInfos(TaskDependentInfos):
    """An object used to store informations about an interface.

    """
    #: Class representing this interface.
    cls = Subclass(BaseInterface)

    #: Widgets associated with this interface.
    views = List()

    #: List of interfaces supported by this task.
    interfaces = Dict()


class ConfigInfos(Atom):
    """An object used to store the informations about a task configurer.

    """
    #: Class representing this configurer.
    cls = Subclass(BaseTask)

    #: Widget associated with this configurer.
    view = Subclass(BaseTaskView)
