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

from .base_tasks import BaseTask, SimpleTask, ComplexTask, RootTask
from .base_views import BaseTaskView
from .task_interface import (InterfaceableTaskMixin, TaskInterface,
                             InterfaceableInterfaceMixin, IInterface)

from .manager.declarations import (Tasks, Task, Interfaces, Interface,
                                   TaskConfig)
from .manager.filters import (TaskFilter, SubclassTaskFilter, GroupTaskFilter,
                              MetadataTaskFilter)

from .manager.configs.base_configs import BaseTaskConfig
from .manager.configs.base_config_views import BaseConfigView

__all__ = ['BaseTask', 'SimpleTask', 'ComplexTask', 'RootTask', 'BaseTaskView',
           'InterfaceableTaskMixin', 'TaskInterface',
           'InterfaceableInterfaceMixin', 'IInterface',
           'Tasks', 'Task', 'Interfaces', 'Interface', 'TaskConfig',
           'TaskFilter', 'SubclassTaskFilter', 'GroupTaskFilter',
           'MetadataTaskFilter', 'BaseTaskConfig', 'BaseConfigView']
