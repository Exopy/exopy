# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Plugin centralizing the collection and managment of tasks and interfaces.

"""
import os
import logging
from collections import defaultdict

from atom.api import List, Dict, Typed, Unicode
from watchdog.observers import Observer

from .declarations import (Task, Interface, Tasks, Interfaces, TaskConfig,
                           TaskConfigs)
from .filters import TaskFilter
from ..utils.plugin_tools import (HasPreferencesPlugin, ExtensionsCollector,
                                  DeclaratorsCollector)
from ..utils.watchdog import SystematicFileUpdater


TASK_EXT_POINT = 'exopy.tasks.declarations'

FILTERS_POINT = 'exopy.tasks.filters'

CONFIG_POINT = 'exopy.tasks.configs'

FOLDER_PATH = os.path.dirname(__file__)


class TaskManagerPlugin(HasPreferencesPlugin):
    """Plugin responsible for collecting and providing tasks.

    """
    #: Known templates (store full path to .ini).
    #: This should not be manipulated by user code.
    templates = Dict()

    #: List of the filters.
    filters = List()

    #: Path to the file in which the names for the tasks are located.
    auto_task_path = Unicode(os.path.join(FOLDER_PATH,
                                          'tasknames.txt')).tag(pref=True)

    #: List of names to use when creating a new task.
    auto_task_names = List()

    def start(self):
        """Collect all declared tasks and start observers.

        """
        super(TaskManagerPlugin, self).start()
        core = self.workbench.get_plugin('enaml.workbench.core')
        core.invoke_command('exopy.app.errors.enter_error_gathering')

        state = core.invoke_command('exopy.app.states.get',
                                    {'state_id': 'exopy.app.directory'})

        t_dir = os.path.join(state.app_directory, 'tasks')
        # Create tasks subfolder if it does not exist.
        if not os.path.isdir(t_dir):
            os.mkdir(t_dir)

        temp_dir = os.path.join(t_dir, 'templates')
        # Create profiles subfolder if it does not exist.
        if not os.path.isdir(temp_dir):
            os.mkdir(temp_dir)

        self._template_folders = [temp_dir]

        self._filters = ExtensionsCollector(workbench=self.workbench,
                                            point=FILTERS_POINT,
                                            ext_class=TaskFilter)
        self._filters.start()
        self.filters = list(self._filters.contributions)

        self._configs = DeclaratorsCollector(workbench=self.workbench,
                                             point=CONFIG_POINT,
                                             ext_class=(TaskConfig,
                                                        TaskConfigs))

        self._configs.start()

        self._tasks = DeclaratorsCollector(workbench=self.workbench,
                                           point=TASK_EXT_POINT,
                                           ext_class=(Tasks, Task, Interfaces,
                                                      Interface)
                                           )
        self._tasks.start()

        self._refresh_templates()
        if self.auto_task_path:
            self.load_auto_task_names()
        self._bind_observers()

        core.invoke_command('exopy.app.errors.exit_error_gathering')

    def stop(self):
        """Discard collected tasks and remove observers.

        """
        self._unbind_observers()
        self._tasks.stop()
        self.templates.clear()
        self._filters.stop()
        self._configs.stop()

    def list_tasks(self, filter='All'):
        """List the known tasks using the specified filter.

        Parameters
        ----------
        filter : unicode, optional
            Name of the filter to use

        Returns
        -------
        tasks : list(unicode) or None
            Task ids selected by the filter, or None if the filter does not
            exist.

        """
        t_filter = self._filters.contributions.get(filter)
        if t_filter:
            return t_filter.filter_tasks(self._tasks.contributions,
                                         self.templates)

    def get_task_infos(self, task):
        """Access a given task infos.

        Parameters
        ----------
        task : unicode
            Id of the task class for which to return the actual class.

        Returns
        -------
        infos : TaskInfos or None
            Object containing all the infos about the requested task.
            This object should never be manipulated directly by user code.

        """
        if task not in self._tasks.contributions:
            return None

        return self._tasks.contributions[task]

    def get_task(self, task, view=False):
        """Access a given task class.

        Parameters
        ----------
        task : unicode
            Id of the task class for which to return the actual class.

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
        infos = self.get_task_infos(task)
        if infos is None:
            answer = None if not view else (None, None)
            return answer

        return infos.cls if not view else (infos.cls, infos.view)

    def get_tasks(self, tasks):
        """Access an ensemble of task classes.

        Parameters
        ----------
        tasks : list(unicode)
            Ids of the task classes for which to return the actual classes.

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

    def get_interface_infos(self, interface):
        """Access a given interface infos.

        Parameters
        ----------
        interface : unicode
            Id of the task this interface is linked to followed by the ids
            of the intermediate interfaces if any and finally id of the
            interface itself. All ids should be separated by ':'
            ex 'exopy.LoopTask:exopy.IterableLoopInterface'

        views : bool, optional
            Whether or not to return the views assoicated with the interface.

        Returns
        -------
        infos : InterfaceInfos
            Object containing all the infos about the requested interface.
            this object should never be manipulated directly by user code.

        """
        lookup_dict = self._tasks.contributions
        ids = interface.split(':')
        interface_id = ids.pop(-1)
        interface_anchor = ids

        try:
            for anchor in interface_anchor:
                lookup_dict = lookup_dict[anchor].interfaces
        except KeyError:
            logger = logging.getLogger(__name__)
            msg = 'Looking for {} (anchor {}) failed to found {}'
            logger.debug(msg.format(interface_id, interface_anchor,
                                    anchor))
            return None

        if interface_id in lookup_dict:
            return lookup_dict[interface_id]
        else:
            return None

    def get_interface(self, interface, views=False):
        """Access a given interface class.

        Parameters
        ----------
        interface: tuple[unicode|tuple|list]
            - Name of the task class for which to return the actual class.
            - Name of the task to which this interface is linked and names of
              the intermediate interfaces if any (going from the most general
              ones to the more specialised ones).

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
        infos = self.get_interface_infos(interface)
        if infos is not None:
            return infos.cls if not views else (infos.cls, infos.views)
        else:
            return None if not views else (None, None)

    def get_interfaces(self, interfaces):
        """Access an ensemble of interface classes.

        Parameters
        ----------
        interfaces : list[tuple[unicode|tuple|list]]
            List of pairs (name of the interface class, corrisponding anchor)
            for which to return the actual classes.

        Returns
        -------
        interfaces_cls : dict
            Dictionary mapping the requested interfaces to the actual classes.

        missing : list
            List of classes that were not found.

        """
        interfaces_cls = {}
        missing = []
        for i in interfaces:
            i_cls = self.get_interface(i)
            if i_cls:
                interfaces_cls[i] = i_cls
            else:
                missing.append(i)

        return interfaces_cls, missing

    def get_config(self, task_id):
        """Access the proper config for a task.

        Parameters
        ----------
        task : unicode
           Id of the task for which a config is required

        Returns
        -------
        config : tuple
            Tuple containing the requested config object, and its
            visualisation.

        """
        templates = self.templates
        if task_id in templates:
            infos = configs = self._configs.contributions['__template__']
            config = infos.cls(manager=self,
                               template_path=templates[task_id])
            return config, infos.view(config=config)

        elif task_id in self._tasks.contributions:
            configs = self._configs.contributions
            # Look up the hierarchy of the selected task to get the appropriate
            # TaskConfig
            task_class = self._tasks.contributions[task_id].cls
            for t_class in type.mro(task_class):
                if t_class in configs:
                    infos = configs[t_class]
                    c = infos.cls(manager=self,
                                  task_class=task_class)
                    return c, infos.view(config=c)

        return None, None

    def load_auto_task_names(self):
        """ Generate a list of task names from a file.

        """
        path = self.auto_task_path
        if not os.path.isfile(path):
            core = self.workbench.get_plugin('enaml.workbench.core')
            msg = 'Path {} does not point to a real file.'.format(path)
            core.invoke_command('exopy.app.errors.signal',
                                dict(kind='error', message=msg))
            return

        with open(path) as f:
            aux = f.readlines()

        self.auto_task_names = [l.rstrip() for l in aux]

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Dictionary storing all known tasks declarartion, using TaskInfos.
    _tasks = Typed(DeclaratorsCollector)

    #: Private storage keeping track of which extension declared which object.
    _extensions = Typed(defaultdict, (list,))

    #: Contributed task filters.
    _filters = Typed(ExtensionsCollector)

    #: Contributed task configs.
    _configs = Typed(DeclaratorsCollector)

    #: List of folders in which to search for templates.
    # TODO make that list editable and part of the preferences
    _template_folders = List()

    #: Watchdog observer tracking changes to the templates folders.
    _observer = Typed(Observer, ())

    def _refresh_templates(self):
        """Refresh the list of template tasks.

        """
        # TODO rework to handle in an nicer fashion same template in multiple
        # folders
        templates = {}
        for path in self._template_folders:
            if os.path.isdir(path):
                filenames = sorted(f for f in os.listdir(path)
                                   if f.endswith('.task.ini') and
                                   (os.path.isfile(os.path.join(path, f))))

                for filename in filenames:
                    template_path = os.path.join(path, filename)
                    # Beware redundant names are overwrited
                    name = filename[:-len('.task.ini')]
                    templates[name] = template_path
            else:
                logger = logging.getLogger(__name__)
                logger.warn('{} is not a valid directory'.format(path))

        self.templates = templates

    def _update_templates(self):
        """Simply refresh the templates task.

        """
        self._refresh_templates()

    def _update_filters(self, change):
        """Update the available list of filters.

        """
        self.filters = list(change['value'].keys())

    def _bind_observers(self):
        """Setup all observers.

        """
        for folder in self._template_folders:
            handler = SystematicFileUpdater(self._update_templates)
            self._observer.schedule(handler, folder, recursive=True)

        self._observer.start()

        self._filters.observe('contributions', self._update_filters)

    def _unbind_observers(self):
        """Remove all observers.

        """
        self._filters.unobserve('contributions', self._update_filters)

        self._observer.unschedule_all()
        self._observer.stop()
        try:
            self._observer.join()
        except RuntimeError:
            pass
