# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Objects used to store tasks, interfaces and configs in the manager.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Atom, List, Subclass, Dict, Coerced
import enaml

from ..base_tasks import BaseTask
from ..task_interface import BaseInterface
from .configs.base_configs import BaseTaskConfig

with enaml.imports():
    from ..base_views import BaseTaskView
    from .configs.base_config_views import BaseConfigView


INSTR_RUNTIME_ID = 'ecpy.instruments'


class ObjectDependentInfos(Atom):
    """Base infos for tasks and interfaces.

    """
    #: List of instrument supported by this task.
    instruments = Coerced(set, ())

    #: Runtime dependencies ids of this object.
    dependencies = List()

    #: List of interfaces supported by this object.
    interfaces = Dict()

    def _post_setattr_instruments(self, old, new):
        if new:
            if INSTR_RUNTIME_ID not in self.dependencies:
                self.dependencies.append(INSTR_RUNTIME_ID)
        elif INSTR_RUNTIME_ID in self.dependencies:
            self.dependencies.remove(INSTR_RUNTIME_ID)


class TaskInfos(ObjectDependentInfos):
    """An object used to store informations about a task.

    """
    #: Class representing this task.
    cls = Subclass(BaseTask)

    #: Widget associated with this task.
    view = Subclass(BaseTaskView)

    #: Metadata associated with this task such as group, looping capabilities,
    #: etc
    metadata = Dict()


class InterfaceInfos(ObjectDependentInfos):
    """An object used to store informations about an interface.

    """
    #: Class representing this interface.
    cls = Subclass(BaseInterface)

    #: Widgets associated with this interface.
    views = List()


class ConfigInfos(Atom):
    """An object used to store the informations about a task configurer.

    """
    #: Class representing this configurer.
    cls = Subclass(BaseTaskConfig)

    #: Widget associated with this configurer.
    view = Subclass(BaseConfigView)
