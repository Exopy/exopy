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

from importlib import import_module
from traceback import format_exc

from atom.api import Unicode, List, Value, Subclass
from enaml.core.api import d_
import enaml

from .base_tasks import BaseTask
from .task_interface import TaskInterface, InterfaceableTaskMixin
from ..utils.declarator import Declarator, GroupDeclarator

with enaml.imports():
    from .base_views import BaseTaskView


class Tasks(GroupDeclarator):
    """GroupDeclarator for tasks.

    Tasks will be stored according to the group of their parent.

    """
    pass


class Task(Declarator):
    """Declarator used to contribute a task.

    """
    #: Path to the task object. Path should be dot separated and the class
    #: name preceded by ':'.
    #: ex: ecpy.tasks.tasks.logic.loop_task:LoopTask
    #: The path of any parent GroupDeclarator object will be prepended to it.
    task = d_(Unicode())

    #: Path to the view object associated with the task.
    #: The path of any parent GroupDeclarator object will be prepended to it.
    view = d_(Unicode())

    #: Task class retrieved at registering time.
    task_cls = Subclass(BaseTask)

    #: View class retrieved at registering time.
    view_cls = Subclass(BaseTaskView)

    def register(self, plugin, traceback):
        """Collect task and view and add itself to the plugin.

        The group declared by a parent if any is taken into account. All
        Interface children are also registered.

        """
        path = self.get_path()
        try:
            t_path, task = (path + '.' + self.task
                            if path else self.task).split(':')
            v_path, view = (path + '.' + self.view
                            if path else self.view).split(':')
        except ValueError:
            msg = 'Incorrect %s (%s), path must be of the form a.b.c:Class'
            if ':' in self.task:
                err_id = self.task.split(':')[1]
                msg = msg % ('view', self.view)
            else:
                err_id = 'Error %d' % len(traceback)
                msg = msg % ('task', self.task)

            traceback[err_id] = msg
            return

        if plugin.task_exists(task) or task in traceback:
            i = 1
            while True:
                err_id = '%s_duplicate%d' % (task, i)
                if err_id not in traceback:
                    break

            msg = 'Duplicate definition of {}, found in {}'
            traceback[err_id] = msg.format(task, t_path)
            return

        try:
            self.task_cls = getattr(import_module(t_path), task)
        except ImportError:
            msg = 'Failed to import {} :\n{}'
            traceback[task] = msg.format(t_path, format_exc())
            return
        except AttributeError:
            msg = '{} has no attribute {}:\n{}'
            traceback[task] = msg.format(t_path, task, format_exc())
            return

        try:
            with enaml.imports():
                self.view_cls = getattr(import_module(v_path), view)
        except ImportError:
            msg = 'Failed to import {} :\n{}'
            traceback[task] = msg.format(v_path, format_exc())
            return
        except AttributeError:
            msg = '{} has no attribute {}:\n{}'
            traceback[task] = msg.format(v_path, view, format_exc())
            return

        if issubclass(self.task_cls, InterfaceableTaskMixin):
            ancestors = type(self.task_cls).mro()
            if ancestors.count(InterfaceableTaskMixin) > 1:
                msg = ('{} cannot inherit multiple times from '
                       'InterfaceableTaskMixin')
                traceback[task] = msg.format(self.task_cls.__name__)

        if any(not isinstance(i, Interface) for i in self.children):
            msg = 'Only Interface can be declared as Task children not {}'
            for err in self.children:
                if not isinstance(i, Interface):
                    break
            traceback[task] = msg.format(type(err))
            return

        plugin._tasks[self.get_group()][task] = self

        for i in self.children:
            i.register(plugin, traceback)

    def unregister(self, plugin):
        """Remove itself from the plugin.

        """
        for i in self.children:
            i.unregister(plugin)
        try:
            del plugin._tasks[self.get_group()][self.task_cls.__name__]
            del self.task_cls
            del self.view_cls
        except KeyError:
            pass


class InstrTask(Task):
    """Declarator used to contribute a task using instruments.

    """
    #: List of supported driver names.
    instrs = List()


class Interfaces(GroupDeclarator):
    """GroupDeclarator for interfaces.

    The group value is not used by interfaces.

    """
    pass


class Interface(Declarator):
    """Declarator for task interfaces.

    An interface can be declared as a child of the task to which its contribute
    in which case the task member can be omitted.

    """
    #: Path to the interface object. Path should be dot separated and the class
    #: name preceded by ':'.
    #: ex: ecpy.tasks.tasks.logic.loop_linspace_interface:LinspaceLoopInterface
    #: The path of any parent GroupDeclarator object will be prepended to it.
    interface = d_(Unicode())

    #: Path or tuple of paths to the view objects associated with the interface
    #: The path of any parent GroupDeclarator object will be prepended to it.
    views = d_(Value())

    #: Name of the task to which this interface contribute.
    task = d_(Unicode())

    #: Interface class retrieved at registering time.
    interface_cls = Subclass(TaskInterface)

    #: View classes retrieved at registering time.
    views_cls = List()

    def register(self, plugin, traceback):
        """Collect interface and views and add itself to the plugin.

        """
        path = self.get_path()
        vs = ([self.views] if not isinstance(self.views, (list, tuple))
              else self.views)
        try:
            i_path, interface = (path + '.' + self.interface
                                 if path else self.interface).split(':')
            if path:
                views = [(path + '.' + v).split(':') for v in vs]
            else:
                views = [(path + '.' + v).split(':') for v in vs]

        except ValueError:
            msg = 'Incorrect %s (%s), path must be of the form a.b.c:Class'
            if self.interface.count(':') == 1:
                err_id = self.interface.split(':')[1]
                msg = msg % ('views', self.views)
            else:
                err_id = 'Error %d' % len(traceback)
                msg = msg % ('interface', self.interface)

            traceback[err_id] = msg
            return

        if plugin.interface_exists(interface) or interface in traceback:
            i = 1
            while True:
                err_id = '%s_duplicate%d' % (interface, i)
                if err_id not in traceback:
                    break

            msg = 'Duplicate definition of {}, found in {}'
            traceback[err_id] = msg.format(interface, i_path)
            return

        try:
            self.interface_cls = getattr(import_module(i_path), interface)
        except ImportError:
            msg = 'Failed to import {} :\n{}'
            traceback[interface] = msg.format(i_path, format_exc())
            return
        except AttributeError:
            msg = '{} has no attribute {}:\n{}'
            traceback[interface] = msg.format(i_path, interface, format_exc())
            return

        try:
            with enaml.imports():
                cls = []
                for v_path, view in views:
                    cls.append(getattr(import_module(v_path), view))
                self.views_cls = cls
        except ImportError:
            msg = 'Failed to import {} :\n{}'
            traceback[interface] = msg.format(v_path, format_exc())
            return
        except AttributeError:
            msg = '{} has no attribute {}:\n{}'
            traceback[interface] = msg.format(v_path, view, format_exc())
            return

        if self.task:
            task = self.task
        elif isinstance(self.parent, Task):
            task = self.parent.task.split(':')[1]
        else:
            traceback[interface] = 'No task declared for {}'.format(interface)
            return

        plugin._interfaces[task].append(self)

    def unregister(self, plugin):
        """Remove itself from the plugin.

        """
        if self.task:
            task = self.task
        elif isinstance(self.parent, Task):
            task = self.parent.task.split(':')[1]
        try:
            del plugin._interface[task][self.interface_cls.__name__]
            del self.interface_cls
            del self.views_cls
        except KeyError:
            pass


class InstrInterface(Interface):
    """Declarator used to contribute a task using instruments.

    """
    #: List of supported driver names.
    instrs = List()
