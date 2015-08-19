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
from collections import OrderedDict
from datetime import date

from future.builtins import str as text
from atom.api import (Instance, Dict, Unicode, Typed, ForwardTyped, Bool,
                      Enum)
from configobj import ConfigObj

from ..tasks.base_tasks import RootTask
from ..utils.configobj_ops import include_configobj
from ..utils.atom_util import HasPrefAtom
from .hooks.internal_checks import InternalChecksHook


logger = logging.getLogger(__name__)


def measure_plugin():
    """Delayed to avoid circular references.

    """
    from .plugin import MeasurePlugin
    return MeasurePlugin


class Measure(HasPrefAtom):
    """Object representing all the aspects of a measure.

    """
    #: Name of the measure.
    name = Unicode().tag(pref=True)

    #: Id of that particular iteration of the measure. This value is used when
    #: saving the measure before running it. It is also communicated to the
    #: root task
    id = Unicode().tag(pref=True)

    #: Flag indicating the measure status.
    status = Enum('READY', 'EDITING', 'SKIPPED', 'FAILED', 'COMPLETED',
                  'INTERRUPTED')

    #: Detailed information about the measure status.
    infos = Unicode()

    #: Path to the last file in which that measure was saved.
    path = Unicode()

    #: Root task holding the measure logic.
    root_task = Instance(RootTask)

    #: Dict of active monitor for this measure.
    monitors = Dict()

    #: Dict of pre-measure execution routines.
    pre_hooks = Typed(OrderedDict, ())

    #: Dict of post-measure execution routines.
    post_hooks = Typed(OrderedDict, ())

    #: Reference to the measure plugin managing this measure.
    plugin = ForwardTyped(measure_plugin)

    #: Flag signaling whether the user chose to enqueue the measure knowing
    #: some tests are failing.
    forced_enqueued = Bool()

    #: Dict to store useful runtime infos
    store = Dict()

    def __init__(self, **kwargs):

        super(Measure, self).__init__(**kwargs)
        self.add_tool('pre_hook', 'internal', InternalChecksHook())

    def save_measure(self, path):
        """Save the measure as a ConfigObj object.

        Parameters
        ----------
        path : unicode
            Path of the file to which save the measure.

        """
        config = ConfigObj(indent_type='    ', encoding='utf-8')
        config.update(self.preferences_from_members())

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
        measure.update_members_from_preferences(**config)

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
            core.invoke_command(err_cmd,
                                dict(kind='measure',
                                     message=msg % (config.get('name'),
                                                    format_exc())))

        for kind in ('monitors', 'pre_hooks', 'post_hooks'):
            saved = config.get(kind, {})

            # Make sure we always have the internal pre-hook in the right
            # position.
            if kind == 'pre_hooks':
                if 'internal' in saved:
                    del measure.pre_hooks['internal']

            for id, state in saved.iteritems():
                obj = measure_plugin.create(kind[:-1], id, bare=True)
                try:
                    obj.set_state(state)
                except Exception:
                    mess = 'Failed to restore {} : {}'.format(kind[:-1],
                                                              format_exc())
                    core.invoke_command(err_cmd,
                                        dict(kind='measure', message=mess))
                    continue
                measure.add_tool(kind[:-1], id, obj)

        measure.name = config.get('name', '')

        return measure

    def run_checks(self, workbench, **kwargs):
        """Run all measure checks.

        This is done at enqueueing time and before actually executing a measure
        save it it was forcibly enqueued.

        Parameters
        ----------
        workbench : Workbench
            Reference to the application workbench.

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

        self.write_infos_in_task()

        msg = 'Running checks for pre-measure hook %s for measure %s'
        for id, hook in self.pre_hooks.iteritems():
            logger.debug(msg, id, self.name)
            answer = hook.check(workbench, self, **kwargs)
            if answer is not None:
                check, errors = answer
                if errors:
                    full_report[id] = errors
                result = result and check

        msg = 'Running checks for post-measure hook %s for measure %s'
        for id, hook in self.post_hooks.iteritems():
            logger.debug(msg, id, self.name)
            answer = hook.check(workbench, self, **kwargs)
            if answer is not None:
                check, errors = answer
                if errors:
                    full_report[id] = errors
                result = result and check

        return result, full_report

    def run_pre_execution(self, workbench, **kwargs):
        """Run pre measure execution operations.

        Those operations consist of the built-in task checks and any
        other operation contributed by a pre-measure hook.

        Parameters
        ----------
        workbench : Workbench
            Reference to the application workbench.

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

        for id, hook in self.pre_hooks.iteritems():
            logger.debug('Calling pre-measure hook %s for measure %s',
                         id, self.name)
            try:
                hook.run(workbench, self, **kwargs)
            except Exception:
                result = False
                full_report[id] = format_exc()

        return result, full_report

    def run_post_execution(self, workbench, **kwargs):
        """Run post measure operations.

        Those operations consist of the operations contributed by
        post-measure hooks.

        Parameters
        ----------
        workbench : Workbench
            Reference to the application workbench.

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
        for id, hook in self.post_hooks.iteritems():
            logger.debug('Calling post-measure hook %s for measure %s',
                         id, self.name)
            try:
                hook.run(workbench, self, **kwargs)
            except Exception:
                result = False
                full_report[id] = format_exc()

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

    def add_tool(self, kind, id, tool=None):
        """Add a tool to the measure.

        Newly added tools are always appended to the list of existing ones.

        Parameters
        ----------
        kind : {'monitor', 'pre_hook', 'post_hook'}
            Kind of tool being added to the measure.

        id : unicode
            Id of the tool being added.

        tool : MeasureTool, optional
            Tool being added, if not specified a new instance will be created.

        """
        if not tool:
            tool = self.plugin.create(kind, id)

        tools = getattr(self, kind + 's').copy()

        if id in tools:
            msg = 'Tool %s is already present in measure %s'
            raise KeyError(msg % (id, self.name))

        tool.link_to_measure(self)

        tools[id] = tool
        setattr(self, kind + 's', tools)

    def move_tool(self, kind, id, new_pos):
        """Modify hooks execution order.

        Parameters
        ----------
        kind : {'pre-hook', 'post-hook'}
            Kind of hook to move.

        id : unicode
            Id of the tool to move.

        new_pos : int
            New index at which the tool should be.

        """
        msg = 'Tool kind must be "pre_hook" or "post_hook" not %s'
        assert kind in ('pre_hook', 'post_hook'), msg % kind

        tools = getattr(self, kind+'s')
        keys = list(tools.keys())
        ind = keys.index(id)
        del keys[ind]
        keys.insert(new_pos, id)

        setattr(self, kind, OrderedDict((k, tools[k]) for k in keys))

    def remove_tool(self, kind, id):
        """Remove a tool.

        Parameters
        ----------
         kind : {'monitor', 'pre_hook', 'post_hook'}
            Kind of tool being added to the measure.

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

    def write_infos_in_task(self):
        """Write all the measure values in the root_task database.

        """
        self.root_task.write_in_database('meas_name', self.name)
        self.root_task.write_in_database('meas_id', self.id)
        self.root_task.write_in_database('meas_date', text(date.today()))

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    def _post_setattr_root_task(self, old, new):
        """Make sure the monitors know the name of the measure.

        """
        new.add_database_entry('meas_name', self.name)
        new.add_database_entry('meas_id', self.id)
        new.add_database_entry('meas_date', '')
