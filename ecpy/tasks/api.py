# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tasks package public interface.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import enaml

from .base_tasks import BaseTask, SimpleTask, ComplexTask, RootTask
from .instr_task import InstrumentTask

from .task_interface import (InterfaceableTaskMixin, TaskInterface,
                             InterfaceableInterfaceMixin, IInterface)

from .manager.declarations import (Tasks, Task, Interfaces, Interface,
                                   TaskConfig)
from .manager.filters import (TaskFilter, SubclassTaskFilter, GroupTaskFilter,
                              MetadataTaskFilter)

from .manager.configs.base_configs import BaseTaskConfig

from .manager.utils.building import build_task_from_config

with enaml.imports():
    from .manager.configs.base_config_views import BaseConfigView
    from .base_views import BaseTaskView
    from .instr_view import InstrTaskView

__all__ = ['BaseTask', 'SimpleTask', 'ComplexTask', 'RootTask',
           'InstrumentTask', 'BaseTaskView', 'InstrTaskView',
           'InterfaceableTaskMixin', 'TaskInterface',
           'InterfaceableInterfaceMixin', 'IInterface',
           'Tasks', 'Task', 'Interfaces', 'Interface', 'TaskConfig',
           'TaskFilter', 'SubclassTaskFilter', 'GroupTaskFilter',
           'MetadataTaskFilter', 'BaseTaskConfig', 'BaseConfigView',
           'build_task_from_config']
