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

from traceback import format_exc
from inspect import cleandoc

from future.utils import python_2_unicode_compatible
from atom.api import Unicode, List, Value, Dict, Property
from enaml.core.api import d_, d_func

from .infos import TaskInfos, InterfaceInfos, ConfigInfos
from ..utils.declarator import Declarator, GroupDeclarator, import_and_get


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
    #: name preceded by ':'.
    #: ex: ecpy.tasks.tasks.logic.loop_task:LoopTask
    #: The path of any parent GroupDeclarator object will be prepended to it.
    #: To update existing TaskInfos (only instruments and interfaces can be
    #: updated that way), one can specify the name of the top level package
    #: in which the task is defined followed by its name.
    #: ex: ecpy.LoopTask
    task = d_(Unicode())

    #: Path to the view object associated with the task.
    #: The path of any parent GroupDeclarator object will be prepended to it.
    view = d_(Unicode())

    #: Metadata associated to the task. ex : loopable = True
    metadata = d_(Dict())

    #: List of supported driver ids.
    instruments = d_(List())

    #: Runtime dependencies analyser ids corresponding to the runtime
    #: dependencies of the task (there is no need to list the instruments
    #: related dependencies as those are handled in a different fashion).
    dependencies = d_(List())

    #: Id of the task computed from the top-level package and the task name
    id = Property(cached=True)

    def register(self, collector, traceback):
        """Collect task and view and add infos to the DeclaratorCollector
        contributions member.

        The group declared by a parent if any is taken into account. All
        Interface children are also registered.

        """
        # Build the task id by assembling the package name and the class name
        task_id = self.id

        # If the task only specifies a name update the matching infos.
        if ':' not in self.task:
            if self.task not in collector.contributions:
                collector._delayed.append(self)
                return

            infos = collector.contributions[task_id]
            infos.instruments.update(self.instruments)
            infos.dependencies.update(self.dependencies)
            infos.metadata.update(self.metadata)

            check = check_children(self)
            if check:
                traceback[task_id] = check
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
            err_id = t_path.split('.', 1)[0] + '.' + task
            msg = msg % ('view', self.view)

            traceback[err_id] = msg
            return

        # Check that the task does not already exist.
        if task_id in collector.contributions or task_id in traceback:
            i = 1
            while True:
                err_id = '%s_duplicate%d' % (task_id, i)
                if err_id not in traceback:
                    break

            msg = 'Duplicate definition of {}, found in {}'
            traceback[err_id] = msg.format(task, t_path)
            return

        infos = TaskInfos(metadata=self.metadata,
                          dependencies=self.dependencies)
        infos.instruments = self.instruments

        # Get the task class.
        t_cls = import_and_get(t_path, task, traceback, task_id)
        if t_cls is None:
            return

        try:
            infos.cls = t_cls
        except TypeError:
            msg = '{} should a subclass of BaseTask.\n{}'
            traceback[task_id] = msg.format(t_cls, format_exc())
            return

        # Get the task view.
        t_view = import_and_get(v_path, view, traceback, task_id)
        if t_view is None:
            return

        try:
            infos.view = t_view
        except TypeError:
            msg = '{} should a subclass of BaseTaskView.\n{}'
            traceback[task_id] = msg.format(t_view, format_exc())
            return

        # Check children type.
        check = check_children(self)
        if check:
            traceback[task_id] = check
            return

        # Add group and add to collector
        infos.metadata['group'] = self.get_group()
        collector.contributions[task_id] = infos

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
                    infos.instruments -= set(self.instruments)
                    infos.dependencies -= set(self.dependencies)

                return

            # Remove infos.
            try:
                # Unparent remaining interfaces
                infos = collector.contributions[self.id]
                for i in infos.interfaces.values():
                    i.parent = None

                del collector.contributions[self.id]
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

    def _get_id(self):
        """Create the unique identifier of the task using the top level package
        and the class name.

        """
        if ':' in self.task:
            path = self.get_path()
            t_path, task = (path + '.' + self.task
                            if path else self.task).split(':')

            # Build the task id by assembling the package name and the class
            # name
            return t_path.split('.', 1)[0] + '.' + task

        else:
            return self.task


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
    #: interface contributes to a task then the task id is enough, if it
    #: contributes to an interface a list with the ids of the tasks and all
    #: intermediate interfaces id should be provided.
    #: When declared as a child of a Task/Interface the names are inferred from
    #: the parents.
    extended = d_(List())

    #: List of supported driver names.
    instruments = d_(List())

    #: Runtime dependencies analyser ids corresponding to the runtime
    #: dependencies of the interface (there is no need to list the instruments
    #: related dependencies as those are handled in a different fashion).
    dependencies = d_(List())

    #: Id of the interface computed from the parents ids and the interface name
    id = Property(cached=True)

    def register(self, collector, traceback):
        """Collect interface and views and add infos to the collector.

        """
        # Update the extended list if necessary.
        if self.extended:
            pass
        elif isinstance(self.parent, Task):
            self.extended = [self.parent.id]
        elif isinstance(self.parent, Interface):
            parent = self.parent
            self.extended = (parent.extended +
                             [parent.id.rsplit(':', 1)[-1]])
        else:
            msg = 'No task/interface declared for {}'
            traceback[self.interface] = msg.format(self.interface)
            return

        # Get access to parent infos.
        try:
            parent_infos = collector.contributions[self.extended[0]]
            for n in self.extended[1::]:
                parent_infos = parent_infos.interfaces[n]

        except KeyError:
            collector._delayed.append(self)
            return

        i_id = self.id
        # Simplified id not including the anchors
        s_id = i_id.rsplit(':', 1)[1]

        # If the interface only specifies a name update the matching infos.
        if ':' not in self.interface:
            if s_id not in parent_infos.interfaces:
                if self.views:
                    msg = 'Incorrect %s (%s), path must be of the form %s'
                    msg = msg % ('interface', self.interface, 'a.b.c:Class')
                    traceback[i_id] = msg
                collector._delayed.append(self)
                return
            infos = parent_infos.interfaces[s_id]
            infos.instruments.update(self.instruments)
            infos.dependencies.update(self.dependencies)

            check = check_children(self)
            if check:
                traceback[i_id] = check
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
            # If interface does not contain ':' it is assumed to be an
            # extension.
            msg = 'Incorrect %s (%s), path must be of the form a.b.c:Class'
            msg = msg % ('views', self.views)

            traceback[i_id] = msg
            return

        # Check that the interface does not already exists.
        if s_id in parent_infos.interfaces or i_id in traceback:
            i = 1
            while True:
                err_id = '%s_duplicate%d' % (i_id, i)
                if err_id not in traceback:
                    break

            msg = 'Duplicate definition of {}, found in {}'
            traceback[err_id] = msg.format(interface, i_path)
            return

        infos = InterfaceInfos(instruments=self.instruments,
                               parent=parent_infos,
                               dependencies=self.dependencies)

        # Get the interface class.
        i_cls = import_and_get(i_path, interface, traceback, i_id)
        if i_cls is None:
            return

        try:
            infos.cls = i_cls
        except TypeError:
            msg = '{} should a subclass of BaseInterface.\n{}'
            traceback[i_id] = msg.format(i_cls, format_exc())
            return

        # Get the views.
        store = []
        v_id = i_id
        counter = 1
        for v_path, view in views:
            if v_id in traceback:
                v_id = i_id + '_%d' % counter
                counter += 1
            view = import_and_get(v_path, view, traceback, v_id)
            if view is not None:
                store.append(view)

        if len(views) != len(store):  # Some error occured
            return
        infos.views = store

        # Check children type.
        check = check_children(self)
        if check:
            traceback[i_id] = check
            return

        parent_infos.interfaces[s_id] = infos

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

            interface = self.id.rsplit(':', 1)[-1]
            if ':' not in self.interface:
                if interface in parent_infos.interfaces:
                    infos = parent_infos.interfaces[interface]
                    infos.instruments -= set(self.instruments)
                    infos.dependencies -= set(self.dependencies)
                return

            try:
                # Unparent remaining interfaces
                infos = parent_infos.interfaces[interface]
                for i in infos.interfaces.values():
                    i.parent = None

                del parent_infos.interfaces[interface]
            except KeyError:
                pass

            self.is_registered = False

    def __str__(self):
        """Nice string representation giving attributes values.

        """
        msg = cleandoc('''{} with:
                       interface: {}, views : {}, extended: {}, instruments {}
                       declaring :
                       {}''')
        return msg.format(type(self).__name__, self.interface, self.views,
                          self.extended, self.instruments,
                          '\n'.join(' - {}'.format(c) for c in self.children))

    def _get_id(self):
        """Create the unique identifier of the interface using the parents ids
        and the class name.

        """
        if ':' in self.interface:
            path = self.get_path()
            i_path, interface = (path + '.' + self.interface
                                 if path else self.interface).split(':')

            # Build the interface name by assembling the package name and the
            # class name
            i_name = i_path.split('.', 1)[0] + '.' + interface
        else:
            i_name = self.interface

        return ':'.join(self.extended + [i_name])


class TaskConfigs(GroupDeclarator):
    """GroupDeclarator for task configs.

    """
    pass


@python_2_unicode_compatible
class TaskConfig(Declarator):
    """Declarator used to declare a task config.

    """
    #: Path to the config object. Path should be dot separated and the class
    #: name preceded by ':'.
    #: ex: ecpy.tasks.config.base_config:PyConfigTask
    #: The path of any parent GroupDeclarator object will be prepended to it.
    config = d_(Unicode())

    #: Path to the view object associated with the task.
    #: The path of any parent GroupDeclarator object will be prepended to it.
    view = d_(Unicode())

    #: Id of the config computed from the top-level package and the config name
    id = Property(cached=True)

    @d_func
    def get_task_class(self):
        """Return the base task class this config is used for.

        """
        raise NotImplementedError()

    def register(self, collector, traceback):
        """Collect config and view and add infos to the DeclaratorCollector
        contributions member under the supported task name.

        """
        # Determine the path to the config and view.
        path = self.get_path()
        try:
            c_path, config = (path + '.' + self.config
                              if path else self.config).split(':')
            v_path, view = (path + '.' + self.view
                            if path else self.view).split(':')
        except ValueError:
            msg = 'Incorrect %s (%s), path must be of the form a.b.c:Class'
            if ':' in self.config:
                msg = msg % ('view', self.view)
            else:
                msg = msg % ('config', self.config)

            traceback[self.id] = msg
            return

        try:
            t_cls = self.get_task_class()
        except Exception:
            msg = 'Failed to get supported task : %s'
            traceback[self.id] = msg % format_exc()
            return

        # Check that the configurer does not already exist.
        if self.id in traceback:
            i = 1
            while True:
                err_id = '%s_duplicate%d' % (config, i)
                if err_id not in traceback:
                    break

            msg = 'Duplicate definition of {}, found in {}'
            traceback[err_id] = msg.format(t_cls, c_path)
            return

        if t_cls in collector.contributions:
            msg = 'Duplicate definition for {}, found in {}'
            traceback[self.id] = msg.format(t_cls, c_path)
            return

        infos = ConfigInfos()

        # Get the config class.
        c_cls = import_and_get(c_path, config, traceback, self.id)
        if c_cls is None:
            return

        try:
            infos.cls = c_cls
        except TypeError:
            msg = '{} should a subclass of BaseTaskConfig.\n{}'
            traceback[self.id] = msg.format(c_cls, format_exc())
            return

        # Get the config view.
        view = import_and_get(v_path, view, traceback, self.id)
        if view is None:
            return

        try:
            infos.view = view
        except TypeError:
            msg = '{} should a subclass of BaseConfigView.\n{}'
            traceback[self.id] = msg.format(view, format_exc())
            return

        collector.contributions[t_cls] = infos

        self.is_registered = True

    def unregister(self, collector):
        """Remove contributed infos from the collector.

        """
        if self.is_registered:
            try:
                del collector.contributions[self.get_task_class()]
            except KeyError:
                pass

            self.is_registered = False

    def __str__(self):
        """Nice string representation giving attributes values.

        """
        msg = cleandoc('''{} with:
                       config: {}, view : {}''')
        return msg.format(type(self).__name__, self.config, self.view)

    def _get_id(self):
        """Create the unique identifier of the config using the top level
        package and the class name.

        """
        if ':' in self.config:
            path = self.get_path()
            c_path, config = (path + '.' + self.config
                              if path else self.config).split(':')

            # Build the task id by assembling the package name and the class
            # name
            return c_path.split('.', 1)[0] + '.' + config

        else:
            return self.config
