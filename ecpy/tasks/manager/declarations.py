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
from inspect import cleandoc

from future.utils import python_2_unicode_compatible
from atom.api import Unicode, List, Value, Dict
from enaml.core.api import d_
import enaml

from .infos import TaskInfos, InterfaceInfos, ConfigInfos
from ...utils.declarator import Declarator, GroupDeclarator


# XXXX modify to allow dependencies declarations

def check_children(declarator):
    """Make sure that all the children of a declarator are interfaces.

    Returns
    -------
    msg : unicode or None
        Error message if one wrongly-typed child was found or None

    """
    # Check children type.
    if any(not isinstance(i, (Interface, Interfaces))
           for i in declarator.children):
        msg = 'Only Interface can be declared as {} children not {}'
        for err in declarator.children:
            if not isinstance(err, Interface):
                break
        return msg.format(type(declarator).__name__, type(err))


class Tasks(GroupDeclarator):
    """GroupDeclarator for tasks.

    Tasks will be stored according to the group of their parent.

    """
    pass


@python_2_unicode_compatible
class Task(Declarator):
    """Declarator used to contribute a task.

    """
    #: Path to the task object. Path should be dot separated and the class
    #: name preceded by ':'. If only the task name is provided it will be used
    #: to update the corresponding TaskInfos (only instruments and interfaces
    #: can be updated that way).
    #: ex: ecpy.tasks.tasks.logic.loop_task:LoopTask
    #: The path of any parent GroupDeclarator object will be prepended to it.
    task = d_(Unicode())

    #: Path to the view object associated with the task.
    #: The path of any parent GroupDeclarator object will be prepended to it.
    view = d_(Unicode())

    #: Metadata associated to the task. ex : loopable = True
    metadata = d_(Dict())

    #: List of supported driver names.
    instruments = d_(List())

    def register(self, collector, traceback):
        """Collect task and view and add infos to the DeclaratorCollector
        contributions member.

        The group declared by a parent if any is taken into account. All
        Interface children are also registered.

        """
        # If the task only specifies a name update the matching infos.
        if ':' not in self.task and '.' not in self.task:
            if self.task not in collector.contributions:
                collector._delayed.append(self)
                return

            infos = collector.contributions[self.task]
            infos.instruments.update(self.instruments)

            check = check_children(self)
            if check:
                traceback[self.task] = check
                return

            for i in self.children:
                i.register(collector, traceback)
            self.is_registered = True
            return

        # Determine the path to the task and view.
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

        # Check that the task does not already exist.
        if task in collector.contributions or task in traceback:
            i = 1
            while True:
                err_id = '%s_duplicate%d' % (task, i)
                if err_id not in traceback:
                    break

            msg = 'Duplicate definition of {}, found in {}'
            traceback[err_id] = msg.format(task, t_path)
            return

        infos = TaskInfos(metadata=self.metadata, instruments=self.instruments)

        # Get the task class.
        try:
            infos.cls = getattr(import_module(t_path), task)
        except ImportError:
            msg = 'Failed to import {} :\n{}'
            traceback[task] = msg.format(t_path, format_exc())
            return
        except AttributeError:
            msg = '{} has no attribute {}:\n{}'
            traceback[task] = msg.format(t_path, task, format_exc())
            return
        except TypeError:
            msg = '{} should a subclass of BaseTask.\n{}'
            traceback[task] = msg.format(task, format_exc())
            return

        # Get the task view.
        try:
            with enaml.imports():
                infos.view = getattr(import_module(v_path), view)
        except ImportError:
            msg = 'Failed to import {} :\n{}'
            traceback[task] = msg.format(v_path, format_exc())
            return
        except AttributeError:
            msg = '{} has no attribute {}:\n{}'
            traceback[task] = msg.format(v_path, view, format_exc())
            return
        except TypeError:
            msg = '{} view should a subclass of BaseTaskView.\n{}'
            traceback[task] = msg.format(task, format_exc())
            return

        # Check children type.
        check = check_children(self)
        if check:
            traceback[task] = check
            return

        # Add group and add to collector
        infos.metadata['group'] = self.get_group()
        collector.contributions[task] = infos

        # Register children.
        for i in self.children:
            i.register(collector, traceback)

        self.is_registered = True

    def unregister(self, collector):
        """Remove contributed infos from the collector.

        """
        if self.is_registered:
            # Unregister children.
            for i in self.children:
                i.unregister(collector)

            # If we were just extending the task, clean instruments.
            if ':' not in self.task:
                if self.task in collector.contributions:
                    infos = collector.contributions[self.task]
                    infos.instruments = [i for i in infos.instruments
                                         if i not in self.instruments]
                return

            # Remove infos.
            task = self.task.split(':')[1]
            try:
                del collector.contributions[task]
            except KeyError:
                pass

            self.is_registered = False

    def __str__(self):
        """Nice string representation giving attributes values.

        """
        msg = cleandoc('''{} with:
                       task: {}, view : {}, metadata: {} and instruments {}
                       declaring :
                       {}''')
        return msg.format(type(self).__name__, self.task, self.view,
                          self.metadata, self.instruments,
                          '\n'.join(' - {}'.format(c) for c in self.children))


class Interfaces(GroupDeclarator):
    """GroupDeclarator for interfaces.

    The group value is not used by interfaces.

    """
    pass


@python_2_unicode_compatible
class Interface(Declarator):
    """Declarator for task interfaces.

    An interface can be declared as a child of the task to which its contribute
    in which case the task member can be omitted.

    """
    #: Path to the interface object. Path should be dot separated and the class
    #: name preceded by ':'. If only the interface name is provided it will be
    #: used to update the corresponding InterfaceInfos.
    #: ex: ecpy.tasks.tasks.logic.loop_linspace_interface:LinspaceLoopInterface
    #: The path of any parent GroupDeclarator object will be prepended to it.
    interface = d_(Unicode())

    #: Path or tuple of paths to the view objects associated with the interface
    #: The path of any parent GroupDeclarator object will be prepended to it.
    views = d_(Value())

    #: Name of the task/interfaces to which this interface contribute. If this
    #: interface contributes to a task then the task name is enough, if it
    #: contributes to an interface a list with the names of the tasks and all
    #: intermediate interfaces should be provided.
    #: When declared as a child of a Task/Interface the names are inferred from
    #: the parents.
    extended = d_(List())

    #: List of supported driver names.
    instruments = d_(List())

    def register(self, collector, traceback):
        """Collect interface and views and add infos to the collector.

        """
        # Update the extended list if necessary.
        if self.extended:
            pass
        elif isinstance(self.parent, Task):
            self.extended = [self.parent.task.split(':')[-1]]
        elif isinstance(self.parent, Interface):
            parent = self.parent
            self.extended = parent.extended + [parent.interface.split(':')[-1]]
        else:
            msg = 'No task/interface declared for {}'
            interface = self.interface.split(':')[-1]
            traceback[interface] = msg.format(interface)
            return
        # Get access to parent infos.
        try:
            parent_infos = collector.contributions[self.extended[0]]
            for n in self.extended[1::]:
                parent_infos = parent_infos.interfaces[n]

        except KeyError:
            collector._delayed.append(self)
            return

        # If the interface only specifies a name update the matching infos.
        if ':' not in self.interface and '.' not in self.interface:
            if self.interface not in parent_infos.interfaces:
                collector._delayed.append(self)
                return
            infos = parent_infos.interfaces[self.interface]
            infos.instruments.update(self.instruments)

            check = check_children(self)
            if check:
                traceback[self.interface] = check
                return

            for i in self.children:
                i.register(collector, traceback)
            self.is_registered = True
            return

        # Determine the path to the interface and views.
        path = self.get_path()
        vs = ([self.views] if not isinstance(self.views, (list, tuple))
              else self.views)
        try:
            i_path, interface = (path + '.' + self.interface
                                 if path else self.interface).split(':')
            if path:
                vs = [path + '.' + v for v in vs]

            views = [v.split(':') for v in vs]
            if any(len(v) != 2 for v in views):
                raise ValueError()

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

        # Check that the interface does not already exists.
        if interface in parent_infos.interfaces or interface in traceback:
            i = 1
            while True:
                err_id = '%s_duplicate%d' % (interface, i)
                if err_id not in traceback:
                    break

            msg = 'Duplicate definition of {}, found in {}'
            traceback[err_id] = msg.format(interface, i_path)
            return

        infos = InterfaceInfos(instruments=self.instruments)

        # Get the interface class.
        try:
            infos.cls = getattr(import_module(i_path), interface)
        except ImportError:
            msg = 'Failed to import {} :\n{}'
            traceback[interface] = msg.format(i_path, format_exc())
            return
        except AttributeError:
            msg = '{} has no attribute {}:\n{}'
            traceback[interface] = msg.format(i_path, interface, format_exc())
            return
        except TypeError:
            msg = 'Interface {} should a subclass of BaseInterface.\n{}'
            traceback[interface] = msg.format(interface, format_exc())
            return

        # Get the views.
        try:
            with enaml.imports():
                cls = []
                for v_path, view in views:
                    cls.append(getattr(import_module(v_path), view))
                infos.views = cls
        except ImportError:
            msg = 'Failed to import {} :\n{}'
            traceback[interface] = msg.format(v_path, format_exc())
            return
        except AttributeError:
            msg = '{} has no attribute {}:\n{}'
            traceback[interface] = msg.format(v_path, view, format_exc())
            return

        # Check children type.
        check = check_children(self)
        if check:
            traceback[interface] = check
            return

        parent_infos.interfaces[interface] = infos

        for i in self.children:
            i.register(collector, traceback)

        self.is_registered = True

    def unregister(self, collector):
        """Remove contributed infos from the collector.

        """
        if self.is_registered:
            try:
                parent_infos = collector.contributions[self.extended[0]]
                for n in self.extended[1::]:
                    parent_infos = parent_infos.interfaces[n]

            except KeyError:
                return

            for i in self.children:
                i.unregister(collector)

            interface = self.interface.split(':')[-1]
            if ':' not in self.interface:
                if interface in parent_infos.interfaces:
                    infos = parent_infos.interfaces[interface]
                    infos.instruments = [i for i in infos.instruments
                                         if i not in self.instruments]
                return

            try:
                del parent_infos.interfaces[interface]
            except KeyError:
                pass

            self.is_registered = False

    def __str__(self):
        """Nice string representation giving attributes values.

        """
        msg = cleandoc('''{} with:
                       interface: {}, view : {}, extended: {}, instruments {}
                       declaring :
                       {}''')
        return msg.format(type(self).__name__, self.task, self.view,
                          self.extended, self.instruments,
                          '\n'.join(' - {}'.format(c) for c in self.children))


@python_2_unicode_compatible
class TaskConfig(Declarator):
    """Declarator used to declare a task config.

    """
    #: Path to the config object. Path should be dot separated and the class
    #: name preceded by ':'.
    #: ex: ecpy.tasks.manager.config.base_config:PyConfigTask
    #: The path of any parent GroupDeclarator object will be prepended to it.
    config = d_(Unicode())

    #: Path to the view object associated with the task.
    #: The path of any parent GroupDeclarator object will be prepended to it.
    view = d_(Unicode())

    #: Name of the task class for which this configurer should be used.
    task = d_(Unicode())

    def register(self, collector, traceback):
        """Collect config and view and add infos to the DeclaratorCollector
        contributions member under the supported task name.

        """
        # Determine the path to the task and view.
        path = self.get_path()
        try:
            c_path, config = (path + '.' + self.config
                              if path else self.config).split(':')
            v_path, view = (path + '.' + self.view
                            if path else self.view).split(':')
        except ValueError:
            msg = 'Incorrect %s (%s), path must be of the form a.b.c:Class'
            if ':' in self.config:
                err_id = self.config.split(':')[1]
                msg = msg % ('view', self.view)
            else:
                err_id = 'Error %d' % len(traceback)
                msg = msg % ('task', self.config)

            traceback[err_id] = msg
            return

        if not self.task:
            traceback[config] = 'Missing supported declaration.'

        # Check that the configurer does not already exist.
        if self.task in collector.contributions or config in traceback:
            i = 1
            while True:
                err_id = '%s_duplicate%d' % (config, i)
                if err_id not in traceback:
                    break

            msg = 'Duplicate definition of {}, found in {}'
            traceback[err_id] = msg.format(config, c_path)
            return

        infos = ConfigInfos()

        # Get the config class.
        try:
            infos.cls = getattr(import_module(c_path), config)
        except ImportError:
            msg = 'Failed to import {} :\n{}'
            traceback[config] = msg.format(c_path, format_exc())
            return
        except AttributeError:
            msg = '{} has no attribute {}:\n{}'
            traceback[config] = msg.format(c_path, config, format_exc())
            return
        except TypeError:
            msg = '{} should a subclass of BaseTaskConfig.\n{}'
            traceback[config] = msg.format(config, format_exc())
            return

        # Get the config view.
        try:
            with enaml.imports():
                infos.view = getattr(import_module(v_path), view)
        except ImportError:
            msg = 'Failed to import {} :\n{}'
            traceback[config] = msg.format(v_path, format_exc())
            return
        except AttributeError:
            msg = '{} config no attribute {}:\n{}'
            traceback[config] = msg.format(v_path, view, format_exc())
            return
        except TypeError:
            msg = '{} view should a subclass of BaseConfigView.\n{}'
            traceback[config] = msg.format(config, format_exc())
            return

        collector.contributions[self.task] = infos

        self.is_registered = True

    def unregister(self, collector, traceback):
        """Remove contributed infos from the collector.

        """
        if self.is_registered:
            try:
                del collector.contributions[self.task]
            except KeyError:
                pass

            self.is_registered = False

    def __str__(self):
        """Nice string representation giving attributes values.

        """
        msg = cleandoc('''{} with:
                       config: {}, view : {}, task: {}''')
        return msg.format(type(self).__name__, self.config, self.view,
                          self.task)
