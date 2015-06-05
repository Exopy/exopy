# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Plugin centralizing the collect and managment of tasks and interfaces.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os
import logging
from collections import defaultdict
from atom.api import List, Dict, Typed, Unicode
from watchdog.observers import Observer

from .declarations import Task, Interface, Tasks, Interfaces
from .filters import TaskFilter
from ...utils.plugin_tools import HasPrefPlugin, ExtensionsCollector
from ...utils.watchdog import SystematicFileUpdater


TASK_EXT_POINT = 'ecpy.tasks.declarations'

FILTERS_POINT = 'ecpy.tasks.filters'

CONFIG_POINT = 'ecpy.tasks.config'

TEMPLATE_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), '..',
                                              'templates'))


class TaskManagerPlugin(HasPrefPlugin):
    """Plugin responsible for collecting and providing tasks.

    """
    #: Dictionary containing all the registering errors.
    errors = Dict()

    #: Folders containings templates which should be loaded.
    templates_folders = List(default=[TEMPLATE_PATH]).tag(pref=True)

    #: Known templates (store full path to .ini).
    #: This should not be manipulated by user code.
    templates = Dict()

    #: List of the filters.
    filters = List()

    #: Path to the file in which the names for the tasks are located.
    auto_task_path = Unicode().tag(pref=True)

    #: List of names to use when creating a new task.
    auto_task_names = List()

    def start(self):
        """Collect all declared tasks and start observers.

        """
        super(TaskManagerPlugin, self).start()
        if not os.path.isdir(TEMPLATE_PATH):
            os.mkdir(TEMPLATE_PATH)

        self._filters = ExtensionsCollector(point=FILTERS_POINT,
                                            ext_cls=TaskFilter,
                                            validate_ext=lambda w, e: True, '')
        self._filters.start()
        # XXXX
#        self._configs = ExtensionsCollector(point=CONFIG_POINT,
#                                            ext_cls=TaskFilter,
#                                            validate_ext=lambda w, e: True, '')
        self._refresh_templates()
        self._load_tasks()
        if self.auto_task_path:
            self.load_auto_task_names()
        self._bind_observers()

    def stop(self):
        """Discard collected tasks and remove observers.

        """
        self._unbind_observers()
        self._tasks.clear()
        self.templates.clear()
        self._filters.stop()
        self._configs.stpp()

    def list_tasks(self, filter='All'):
        """List the known tasks using the specified filter.

        Parameters
        ----------
        filter_name : unicode, optional
            Name of the filter to use

        Returns
        -------
        tasks : list(str) or None
            Tasks selected by the filter, or None if the filter does not exist.

        """
        t_filter = self._filters.get(filter)
        if t_filter:
            return t_filter.list_tasks(self._tasks, self.templates)

    def get_task_infos(self, task_class_name):
        """Access a given task infos.

        Parameters
        ----------
        task_cls_name : unicode
            Name of the task class for which to return the actual class.

        Returns
        -------
        infos : TaskInfos or None
            Object containing all the infos about the requested task.
            This object should never be manipulated directly by user code.

        """
        if task_cls_name not in self._tasks:
            return None

        return self._tasks[task_cls_name]

    def get_task(self, task_cls_name, view=False):
        """Access a given task class.

        Parameters
        ----------
        task_cls_name : unicode
            Name of the task class for which to return the actual class.

        view : bool, optional
            Whether or not to return the view assoicated with the task.

        Returns
        -------
        task_cls : type or None
            Class associated to the requested task or None if the task was not
            found.

        task_view : EnamlDefMeta or None, optional
            Associated view if requested.

        """
        infos = self.get_task_infos(task_cls_name)
        if infos is not None:
            answer = None if not view else (None, None)
            return answer

        return infos.cls if not view else (infos.cls, infos.view)

    def get_tasks(self, tasks):
        """Access an ensemble of task classes.

        Parameters
        ----------
        tasks : list(unicode)
            Names of the task classes for which to return the actual classes.

        Returns
        -------
        tasks_cls : dict
            Dictionary mapping the requested tasks to the actual classes.

        missing : list
            List of classes that were not found.

        """
        tasks_cls = {}
        missing = []
        for t in tasks:
            res = self.get_task(t)
            if res:
                tasks_cls[t] = res
            else:
                missing.append(t)

        return tasks_cls, missing

    def get_interface_infos(self, interface_cls_name, anchor):
        """Access a given interface infos.

        Parameters
        ----------
        interface_cls_name : unicode
            Name of the task class for which to return the actual class.

        interface_anchor : unicode or list
            Name of the task to which this interface is linked and names of the
            intermediate interfaces if any (going from the most general ones
            to the more specialised ones).

        views : bool, optional
            Whether or not to return the views assoicated with the interface.

        Returns
        -------
        infos : InterfaceInfos
            Object containing all the infos about the requested interface.
            this object should never be manipulated directly by user code.

        """
        lookup_dict = self._tasks
        if not isinstance(interface_anchor, (list, tuple)):
            interface_anchor = [interface_anchor]

        try:
            for anchor in interface_anchor:
                lookup_dict = lookup_dict[anchor]
        except KeyError:
            logger = logging.getLogger(__name__)
            msg = 'Looking for {} (anchor {}) failed to found {}'
            logger.debug(msg.format(interface_cls_name, interface_anchor,
                                    anchor))
            return None if not views else (None, None)

        if interface_cls_name in lookup_dict:
            return lookup_dict[interface_cls_name]
        else:
            return None

    def get_interface(self, interface_cls_name, interface_anchor, views=False):
        """Access a given interface class.

        Parameters
        ----------
        interface_cls_name : unicode
            Name of the task class for which to return the actual class.

        interface_anchor : unicode or list
            Name of the task to which this interface is linked and names of the
            intermediate interfaces if any (going from the most general ones
            to the more specialised ones).

        views : bool, optional
            Whether or not to return the views assoicated with the interface.

        Returns
        -------
        interface_cls : type or None
            Class corresponding to the requested interface or None if the class
            was not found.

        views : list or None, optional
            List of views associated with the interface.

        """
        infos = self.get_interface_infos(interface_cls_name, anchor)
        if infos is not None:
            return infos.cls if not views else (infos.cls, infos.views)
        else:
            return None if not views else (None, None)

    def get_interfaces(interfaces, anchors):
        """Access an ensemble of interface classes.

        Parameters
        ----------
        interfaces : list(unicode)
            Names of the interface classes for which to return the actual
            classes.

        anchor : list(list(unicode))
            Anchor corresponding to each requested interface.

        Returns
        -------
        interfaces_cls : dict
            Dictionary mapping the requested interfaces to the actual classes.

        missing : list
            List of classes that were not found.

        """
        interfaces_cls = {}
        missing = []
        for i, a in zip(interfaces, anchors):
            i_cls = self.get_interface(i, a)
            if i_cls:
                interfaces_cls[i] = i_cls
            else:
                missing.append(i)

        return interfaces_cls, missing

    def get_config(self, task):
        """ Access the proper config for a task.

        Parameters
        ----------
        task : unicode or type
            Name or class of the task for which a config is required

        Returns
        -------
        config : tuple
            Tuple containing the requested config object, and its
            visualisation.

        """
        # XXXXX rework once config are back in the game
        if isinstance(task, type):
            task = task.__name__

        templates = self._template_tasks
        if task in self._template_tasks:
            return IniConfigTask(manager=self,
                                 template_path=templates[task]), IniView

        elif task in self._tasks:
            configs = self._configs
            # Look up the hierarchy of the selected task to get the appropriate
            # TaskConfig
            task_class = self._tasks[task].cls
            for t_class in type.mro(task_class):
                if t_class in configs:
                    config = configs[t_class][0]
                    view = configs[t_class][1]
                    return config(manager=self,
                                  task_class=task_class), view

        return None, None

    def load_auto_task_names(self, path=None):
        """ Generate a list of task names from a file.

        Parameters
        ----------
        path : unicode, optional
            Path from which to load the default task names. If not provided
            the auto_task_path is used.

        Returns
        -------
        result : bool
            Flag indicating whether or not the operation succeeded

        """
        if not path:
            path = self.auto_task_path
        if not os.path.isfile(path):
            logger = logging.getLogger(__name__)
            logger.warn('Path {} does not point to a real file.'.format(path))
            return False

        with open(path) as f:
            aux = f.readlines()

        self.auto_task_names = [l.rstrip() for l in aux]
        return True

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Dictionary storing all known tasks declarartion, using TaskInfos.
    _tasks = Dict()

    #: Private storage keeping track of which extension declared which object.
    _extensions = Typed(defaultdict, (list,))

    #: Contributed task filters.
    _filters = Typed(ExtensionsCollector)

    #: Contributed task configs.
    _configs = Typed(ExtensionsCollector)

    #: Watchdog observer tracking changes to the templates folders.
    _observer = Typed(Observer, ())

    def _refresh_templates(self):
        """Refresh the list of template tasks.

        """
        # XXXX rework to handle in an nicer fashion same template in multiple
        # folders
        templates = {}
        for path in self.templates_folders:
            if os.path.isdir(path):
                filenames = sorted(f for f in os.listdir(path)
                                   if f.endswith('.ini') and
                                   (os.path.isfile(os.path.join(path, f))))

                for filename in filenames:
                    template_path = os.path.join(path, filename)
                    # Beware redundant names are overwrited
                    templates[filename] = template_path
            else:
                logger = logging.getLogger(__name__)
                logger.warn('{} is not a valid directory'.format(path))

        self._template = templates

    def _load_tasks(self):
        """Load all the task definitions contributed by extensions.

        """
        workbench = self.workbench
        point = workbench.get_extension_point(self.point)
        extensions = point.extensions

        # If no extension remain clear everything
        if not extensions:
            # Force a notification to be emitted.
            self._tasks.clear()
            self._extensions.clear()
            return

        self._register_task_decls(extensions)

    # XXXX refactor in plugin tools as I need it also for config and will also
    # need it for instruments.
    def _register_task_decls(self, extensions):
        """Register the task declaration linked to some extensions.

        Handle multiple registerin attempts.

        """
        # Get the tasks and interfaces declarations for all extensions.
        new_extensions = defaultdict(list)
        old_extensions = self._extensions
        for extension in extensions:
            if extension not in old_extensions:
                declarators = self._get_task_decls(extension)
            new_extensions[extension].extend(declarators)

        # Register all contributions.
        tb = {}
        for extension in new_extensions:
            for declarator in new_extensions[extension]:
                declarator.regsiter(self, tb)

        old = 0
        while self._delayed and old != len(self._delayed):
            for declarator in self._delayed:
                declarator.register(self, tb)

        if self._delayed:
            msg = 'Some declarations have not been registered : {}'
            tb['Missing declarations'] = msg.format(self._delayed)

        self.errors.update(tb)
        self._extensions.update(new_extensions)

    def _get_task_decls(self, extension):
        """Get the task declarations declared by an extension.

        """
        workbench = self.workbench
        contribs = extension.get_children((Task, Interface, Tasks, Interfaces))
        if extension.factory is not None and not contribs:
            for contrib in extension.factory(workbench):
                if not isinstance(contrib,
                                  (Task, Interface, Tasks, Interfaces)):
                    msg = "Extension '{}' should create {} not {}."
                    valids = ('Task', 'Interface', 'Tasks', 'Interfaces')
                    raise TypeError(msg.format(extension.qualified_id,
                                               valids, type(contrib).__name__))
                contribs.append(contrib)

        return contribs

    def _unregister_task_decls(self, extensions):
        """Unregister the task declaration linked to some extensions.

        """
        for extension in extensions:
            for declarator in extensions[extension]:
                declarator.unregsiter(self)

    def _post_setattr_template_folders(self):
        """Ensure that the template observer always watch the right folder.

        """
        self._observer.unschedule_all()

        for folder in self.templates_folders:
            handler = SystematicFileUpdater(self._update_templates)
            self._observer.schedule(handler, folder, recursive=True)

    def _update_templates(self):
        """Simply refresh the templates task.

        """
        self._refresh_template_tasks()

    def _update_tasks(self, change):
        """Update the known tasks when a contribution is added/removed.

        """
        old = change.get('oldvalue')
        new = change['value']
        added = new - old
        removed = old - new
        self._unregister_task_decls((ext for ext in self._extensions
                                     if ext in removed))

        self._register_task_decls(added)

    def _update_filters(self, change):
        """Update the available list of filters.

        """
        self.filters = list(change['value'].keys())

    def _bind_observers(self):
        """Setup all observers.

        """
        for folder in self.templates_folders:
            handler = SystematicFileUpdater(self._update_templates)
            self._observer.schedule(handler, folder, recursive=True)

        self._observer.start()

        workbench = self.workbench
        point = workbench.get_extension_point(TASK_EXT_POINT)
        point.observe('extensions', self._update_tasks)

        self._filters.observe('contributions', self._update_filters)

    def _unbind_observers(self):
        """Remove all observers.

        """
        self._filters.unobserve('contributions', self._update_filters)

        workbench = self.workbench
        point = workbench.get_extension_point(TASK_EXT_POINT)
        point.unobserve('extensions', self._update_tasks)

        self._observer.unschedule_all()
        self._observer.stop()
        try:
            self._observer.join()
        except RuntimeError:
            pass
