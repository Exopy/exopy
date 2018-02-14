# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Objects used to store tasks, interfaces and configs in the manager.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import (Atom, List, Subclass, Dict, Coerced, Typed, Unicode,
                      set_default)
import enaml

from .tasks.base_tasks import BaseTask
from .tasks.task_interface import BaseInterface
from .configs.base_configs import BaseTaskConfig

with enaml.imports():
    from .tasks.base_views import BaseTaskView
    from .configs.base_config_views import BaseConfigView


INSTR_RUNTIME_TASK_DRIVERS_ID = 'exopy.tasks.instruments.drivers'

INSTR_RUNTIME_TASK_PROFILES_ID = 'exopy.tasks.instruments.profiles'

INSTR_RUNTIME_INTERFACE_DRIVERS_ID =\
    'exopy.tasks.interface.instruments.drivers'

INSTR_RUNTIME_INTERFACE_PROFILES_ID =\
    'exopy.tasks.interface.instruments.profiles'


class ObjectDependentInfos(Atom):
    """Base infos for tasks and interfaces.

    """
    #: Id of the runtime dependency analyser to use for driver detection to add
    #: to the dependencies if instruments is set.
    DRIVER_ANALYSER = Unicode()

    #: Id of the runtime dependency analyser to use for profile detection to
    #: add to the dependencies if instruments is set.
    PROFILE_ANALYSER = Unicode()

    #: Set of instrument supported by this task. This should never be updated
    #: in place, it should always be copied and replaced by the new value.
    instruments = Coerced(set, ())

    #: Runtime dependencies ids of this object.
    dependencies = Coerced(set, ())

    #: Dict of interfaces supported by this object as {id: InterfaceInfos}.
    interfaces = Dict()

    def __init__(self, **kwargs):
        super(ObjectDependentInfos, self).__init__(**kwargs)
        if self.instruments:
            self._post_setattr_instruments(set(), self.instruments)

    def walk_interfaces(self, depth=None):
        """Yield all the interfaces of a task/interfaces.

        Parameters
        ----------
        depth : int | None
            Interface depth at which to stop.

        """
        for i_id, i in self.interfaces.items():
            yield i_id, i
            if depth is None or depth > 0:
                d = depth - 1 if depth else None
                for ii_id, ii in i.walk_interfaces(d):
                    yield ii_id, ii

    def _post_setattr_instruments(self, old, new):
        """Update the dependencies each time the instruments member is set.

        """
        if new:
            self.dependencies |= set((self.DRIVER_ANALYSER,
                                      self.PROFILE_ANALYSER))
        else:
            self.dependencies -= set((self.DRIVER_ANALYSER,
                                      self.PROFILE_ANALYSER))


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

    DRIVER_ANALYSER = set_default(INSTR_RUNTIME_TASK_DRIVERS_ID)

    PROFILE_ANALYSER = set_default(INSTR_RUNTIME_TASK_PROFILES_ID)


class InterfaceInfos(ObjectDependentInfos):
    """An object used to store informations about an interface.

    """
    #: Class representing this interface.
    cls = Subclass(BaseInterface)

    #: Widgets associated with this interface.
    views = List()

    #: Parent task or interface infos.
    parent = Typed(ObjectDependentInfos)

    DRIVER_ANALYSER = set_default(INSTR_RUNTIME_INTERFACE_DRIVERS_ID)

    PROFILE_ANALYSER = set_default(INSTR_RUNTIME_INTERFACE_PROFILES_ID)


class ConfigInfos(Atom):
    """An object used to store the informations about a task configurer.

    """
    #: Class representing this configurer.
    cls = Subclass(BaseTaskConfig)

    #: Widget associated with this configurer.
    view = Subclass(BaseConfigView)
