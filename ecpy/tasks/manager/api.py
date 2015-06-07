# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Exposed interface of the task manager.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from .declarations import Tasks, Task, Interfaces, Interface, TaskConfig
from .filters import (TaskFilter, SubclassTaskFilter, GroupTaskFilter,
                      MetadataTaskFilter)

from ..configs.base_configs import BaseTaskConfig
from ..configs.base_config_views import BaseConfigView

__all__ = ['Tasks', 'Task', 'Interfaces', 'Interface', 'TaskConfig',
           'TaskFilter', 'SubclassTaskFilter', 'GroupTaskFilter',
           'MetadataTaskFilter', 'BaseTaskConfig', 'BaseConfigView']
