# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tasks package public interface.

"""
import enaml

from .tasks.base_tasks import BaseTask, SimpleTask, ComplexTask, RootTask
from .tasks.instr_task import InstrumentTask

from .tasks.task_interface import (InterfaceableTaskMixin, TaskInterface,
                                   InterfaceableInterfaceMixin, IInterface)
from .tasks.string_evaluation import FORMATTER_TOOLTIP, EVALUATER_TOOLTIP

from .tasks import validators

from .declarations import (Tasks, Task, Interfaces, Interface,
                           TaskConfig)
from .filters import (TaskFilter, SubclassTaskFilter, GroupTaskFilter,
                      MetadataTaskFilter)

from .configs.base_configs import BaseTaskConfig

from .utils.building import build_task_from_config

with enaml.imports():
    from .configs.base_config_views import BaseConfigView
    from .tasks.base_views import BaseTaskView
    from .tasks.instr_view import InstrTaskView

__all__ = ['BaseTask', 'SimpleTask', 'ComplexTask', 'RootTask',
           'InstrumentTask', 'BaseTaskView', 'InstrTaskView',
           'InterfaceableTaskMixin', 'TaskInterface',
           'InterfaceableInterfaceMixin', 'IInterface',
           'Tasks', 'Task', 'Interfaces', 'Interface', 'TaskConfig',
           'TaskFilter', 'SubclassTaskFilter', 'GroupTaskFilter',
           'MetadataTaskFilter', 'BaseTaskConfig', 'BaseConfigView',
           'build_task_from_config', 'validators',
           'FORMATTER_TOOLTIP', 'EVALUATER_TOOLTIP']
