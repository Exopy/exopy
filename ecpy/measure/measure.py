# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""A measure represent all the components of a measure from the task hierarchy
to the tools such as headers, monitors and checks.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import logging
from traceback import format_exc

from atom.api import Atom, Instance, Dict, Unicode, ForwardTyped, Enum
from configobj import ConfigObj

from ecpy.tasks.base_tasks import RootTask
from ecpy.utils.configobj_ops import include_configobj


logger = logging.getLogger(__name__)


def measure_plugin():
    """Delayed to avoid circular references.

    """
    from .plugin import MeasurePlugin
    return MeasurePlugin


class Measure(Atom):
    """Object representing all the aspects of a measure.

    """
    #: Name of the measure. This value is synchronized with the ones found
    #: in the root task and the monitors.
    name = Unicode()

    #: Flag indicating the measure status.
    status = Enum()

    #: Detailed information about the measure status.
    infos = Unicode()

    #: Path to the last file in which that measure was saved.
    path = Unicode()

    #: Root task holding the measure logic.
    root_task = Instance(RootTask)

    #: Dict of active monitor for this measure.
    monitors = Dict()

    #: Dict of pre-measure execution routines.
    pre_hooks = Dict()

    #: Dict of post-measure execution routines.
    post_hooks = Dict()

    #: Reference to the measure plugin managing this measure.
    plugin = ForwardTyped(measure_plugin)

    #: Dict to store useful runtime infos
    store = Dict()

    def save_measure(self, path):
        """Save the measure as a ConfigObj object.

        Parameters
        ----------
        path : unicode
            Path of the file to which save the measure.

        """
        config = ConfigObj(indent_type='    ', encoding='utf-8')

        # First save the task.
        core = self.plugin.workbench.get_plugin(u'enaml.workbench.core')
        cmd = u'ecpy.tasks.save'
        task_prefs = core.invoke_command(cmd, {'task': self.root_task,
                                               'mode': 'config'}, self)
        config['root_task'] = {}
        include_configobj(config['root_task'], task_prefs)

        # Save the state of each monitor, pre-hook, post-hook.
        for kind in ('monitors', 'pre_hooks', 'post_hooks'):
            config[kind] = {}
            for id, obj in getattr(self, kind).iteritems():
                state = obj.get_state()
                config[kind][id] = {}
                include_configobj(config[kind][id], state)

        # Also save the name of the measure for readability purposes.
        config['name'] = self.root_task.meas_name

        with open(path, 'w') as f:
            config.write(f)

        self.path = path

    @classmethod
    def load_measure(cls, measure_plugin, path, build_dep=None):
        """Build a measure from a ConfigObj file.

        Parameters
        ----------
        measure_plugin : MeasurePlugin
            Instance of the MeasurePlugin storing all declarations.

        path : unicode
            Path of the file from which to load the measure.

        """
        # Create the measure.
        measure = cls()
        config = ConfigObj(path)
        measure.plugin = measure_plugin
        measure.path = path

        # Gather all errors occuring while loading the measure.
        workbench = measure_plugin.workbench
        core = workbench.get_plugin(u'enaml.workbench.core')
        cmd = 'ecpy.app.errors.enter_error_gathering'
        core.invoke_command(cmd)
        err_cmd = 'ecpy.app.errors.signal'

        # Load the task.
        cmd = u'hqc_meas.task_manager.build_root'
        kwarg = {'mode': 'config', 'config': config['root_task'],
                 'build_dep': build_dep}
        try:
            measure.root_task = core.invoke_command(cmd, kwarg, measure)
        except Exception:
            msg = 'Building %s, failed to restore task : %s'
            # TODO think of a nice error reporting
            core.invoke_command(err_cmd,
                                dict(kind='measure',
                                     msg=msg % (config.get('name'),
                                                format_exc())))

        for kind in ('monitors', 'pre-hooks', 'post-hooks'):
            saved = config.get(kind, {})
            for id, state in saved.iteritems():
                obj = measure_plugin.create(kind[:-1], id, bare=True)
                try:
                    obj.set_state(state, measure)
                except Exception:
                    mess = 'Failed to restore {} : {}'.format(kind[:-1],
                                                              format_exc())
                    # TODO think of a nice error reporting
                    core.invoke_command(err_cmd,
                                        dict(kind='measure', msg=mess))
                    continue
                measure.add_tool(kind[:-1], id, obj)

        measure.name = config.get('name', '')

        return measure

    def run_pre_measure(self, workbench, scope='complete', **kwargs):
        """Run pre measure operations.

        Those operations consist of the built-in task checks and any
        other operation contributed by a pre-measure hook.

        Parameters
        ----------
        workbench : Workbench
            Reference to the application workbench.

        scope : unicode, optional
            Flag used to specify which pre-measure operations run. By default
            all operations are run. To only run the built-in tasks checks use
            'internal'. Any other value will be interpreted as a hook kind and
            only the hooks of that kind will be run.

        **kwargs :
            Keyword arguments to pass to the pre-operations.

        Returns
        -------
        result : bool
            Boolean indicating whether or not the operations succeeded.

        report : dict
            Dict storing the errors (as dict) by id of the operation in which
            they occured.

        """
        result = True
        full_report = {}

        if scope in ('internal', 'complete'):
            logger.debug('Running internal checks for measure %s',
                         self.name)
            check, errors = self.root_task.check(**kwargs)
            if errors:
                full_report['internal'] = errors
            result = result and check
            if scope == 'internal':
                return result, full_report

        pre_hooks = ({k: v for k, v in self.pre_hooks.iteritems()
                     if v.declaration.kind == scope}
                     if scope != 'complete' else self.pre_hooks)

        for id, hook in pre_hooks.iteritems():
            logger.debug('Calling pre-measure hook %s for measure %s',
                         id, self.name)
            answer = hook.run(workbench, self, **kwargs)
            if answer is not None:
                check, errors = answer
                if errors:
                    full_report[id] = errors
                result = result and check

        return result, full_report

    def run_post_measure(self, workbench, scope='complete', **kwargs):
        """Run post measure operations.

        Those operations consist of the operations contributed by
        post-measure hooks.

        Parameters
        ----------
        workbench : Workbench
            Reference to the application workbench.

        scope : unicode, optional
            Flag used to specify which post-measure operations run. By default
            all operations are run. A non default value will be interpreted as
            a hook kind and only the hooks of that kind will be run.

        **kwargs :
            Keyword arguments to pass to the post-operations.

        Returns
        -------
        result : bool
            Boolean indicating whether or not the operations succeeded.

        report : dict
            Dict storing the errors (as dict) by id of the operation in which
            they occured.

        """
        result = True
        full_report = {}
        post_hooks = ({k: v for k, v in self.pre_hooks.iteritems()
                      if v.declaration.kind == scope}
                      if scope != 'complete' else self.post_hooks)

        for id, hook in post_hooks.iteritems():
            logger.debug('Calling post-measure hook %s for measure %s',
                         id, self.name)
            answer = hook.run(workbench, self, **kwargs)
            if answer is not None:
                check, errors = answer
                if errors:
                    full_report[id] = errors
                result = result and check

        return result, full_report

    def enter_edition_state(self):
        """Make the the measure ready to be edited

        """
        database = self.root_task.database
        for monitor in self.monitors.values():
            if not database.has_observer('notifier',
                                         monitor.database_modified):
                database.observe('notifier', monitor.database_modified)

    def enter_running_state(self):
        """Make the measure ready to run.

        """
        database = self.root_task.database
        for monitor in self.monitors.values():
            if database.has_observer('notifier', monitor.database_modified):
                database.unobserve('notifier', monitor.database_modified)

    def add_tool(self, kind, id, tool, refresh=True):
        """Add a tool to the measure.

        Parameters
        ----------
        kind : {'monitor', 'pre_hook', 'post_hook'}
            Kind of tool beinig added to the measure.

        id : unicode
            Id of the tool being added.

        tool : MeasureTool
            Tool being added.

        """
        tools = getattr(self, kind + 's').copy()

        if id in tools:
            msg = 'Tool %s is already present in measure %s'
            raise KeyError(msg % (id, self.name))

        tool.link_to_measure(self)

        tools[id] = tool
        setattr(self, kind + 's', tools)

    def remove_tool(self, kind, id):
        """Remove a tool.

        Parameters
        ----------
        id : unicode
            Id of the monitor to remove.

        """
        tools = getattr(self, kind + 's').copy()

        if id not in tools:
            msg = 'Tool %s is not present in measure %s'
            raise KeyError(msg % (id, self.name))

        tools[id].unlink_from_measure(self)

        del tools[id]
        setattr(self, kind + 's', tools)

    def collect_entries_to_observe(self):
        """Get all the entries the monitors ask to be notified about.

        Returns
        -------
        entries : list
            List of the entries the engine will to observe.

        """
        entries = []
        for monitor in self.monitors.values():
            entries.extend(monitor.database_entries)

        return list(set(entries))

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    def _post_setattr_root_task(self, old, new):
        """Make sure that the monitors observe the right database.

        """
        monitors = self.monitors.values()
        if old:
            # Stop observing the database (remove all handlers)
            old.task_database.unobserve('notifier')

        root = new
        database = root.task_database
        for monitor in monitors:
            monitor.clear_state()
            root.task_database.observe('notifier',
                                       monitor.database_modified)

            database_entries = database.list_all_entries(values=True)
            monitor.refresh_monitored_entries(database_entries)

    def _post_setattr_status(self, old, new):
        """Update the monitors' status when the measure is run.

        """
        if new:
            for monitor in self.monitors.values():
                monitor.measure_status = new

    def _post_setattr_name(self, old, new):
        """Make sure the monitors know the name of the measure.

        """
        self.root_task.meas_name = new

        for monitor in self.monitors.values():
            monitor.measure_name = new
