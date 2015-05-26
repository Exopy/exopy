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
from ..task_interface import TaskInterface

with enaml.imports():
    from ..base_views import BaseTaskView


class TaskInfos(Atom):
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

    #: List of instrument supported by this task.
    instruments = Coerced(set, ())


class InterfaceInfos(Atom):
    """An object used to store informations about an interface.

    """
    #: Class representing this interface.
    cls = Subclass(TaskInterface)

    #: Widgets associated with this interface.
    views = List()

    #: List of interfaces supported by this task.
    interfaces = Dict()

    #: List of instrument supported by this task.
    instruments = Coerced(set, ())
