# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Main objects used to represent all the aspects of a measure (main task,
 attached tools, dependencies, ...)

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import logging
from traceback import format_exc
from collections import OrderedDict, defaultdict
from itertools import chain
from datetime import date

from future.builtins import str as text
from atom.api import (Atom, Dict, Unicode, Typed, ForwardTyped, Bool, Enum,
                      Value)
from configobj import ConfigObj

from ..tasks.base_tasks import RootTask
from ..utils.configobj_ops import include_configobj
from ..utils.atom_util import HasPrefAtom


logger = logging.getLogger(__name__)


def measure_plugin():
    """Delayed to avoid circular references.

    """
    from .plugin import MeasurePlugin
    return MeasurePlugin


class MeasureDependencies(Atom):
    """Container used to store the dependencies of a measure.

    """
    #: Reference to the Measure this object is linked to.
    measure = ForwardTyped(lambda: Measure)

    def collect_runtimes(self):
        """Collect all the runtime needed to execute the measure.

        Those can then be accessed using `get_runtime_dependencies`

        Returns
        -------
        result : bool
            Boolean indicating whether or not the collection succeeded. Note
            that even if the collection failed, some dependencies may have been
            collected (other being unavailable) and must hance be released.

        msg : unicode
            String explaning why the operation failed if it failed.

        errors : dict
            Dictionary describing in details the errors. If some dependencies
            does exist but cannot be accessed at the time of the query an entry
            'unavailable' will be present.

        """
        if self._runtime_dependencies:
            return True, '', {}

        workbench = self.measure.plugin.workbench
        core = workbench.get_plugin('enaml.workbench.core')

        # If the dependencies of the main task are not known
        if not self._runtime_map.get('main'):
            cmd = 'ecpy.app.dependencies.analyse'
            deps = core.invoke_command(cmd,
                                       {'obj': self.measure.root_task,
                                        'dependencies': ['build', 'runtime']})

            b_deps, r_deps = deps
            msg = 'Failed to analyse main task %s dependencies.'
            if b_deps.errors:
                return False, msg % 'build', b_deps.errors
            if r_deps.errors:
                return False, msg % 'runtime', r_deps.errors
            self._build_analysis = b_deps.dependencies
            self._runtime_map['main'] = r_deps.dependencies
            self._update_runtime_analysis(r_deps.dependencies)

        # Check that we know the dependencies of the hooks
        for h_id, h in chain(self.measure.pre_hooks.items(),
                             self.measure.post_hooks.items()):
            if h_id not in self._runtime_map:
                deps = h.list_runtimes(workbench)

                if deps is None:
                    continue  # The hook has no runtime dependencies

                if deps.errors:
                    msg = 'Failed to analyse hook %s runtime dependencies.'
                    return False, msg % h_id, deps.errors

                self._runtime_map[h_id] = deps.dependencies
                self._update_runtime_analysis(deps.dependencies)

        cmd = 'ecpy.app.dependencies.collect'
        deps = core.invoke_command(cmd,
                                   dict(dependencies=self._runtime_analysis,
                                        owner='ecpy.measure', kind='runtime'))

        if deps.errors:
            msg = 'Failed to collect some runtime dependencies.'
            return False, msg, deps.errors

        elif deps.unavailable:
            msg = 'Some dependencies are currently unavailable.'
            self._runtime_dependencies = deps.dependencies
            return False, msg, deps.unavailable

        self._runtime_dependencies = deps.dependencies
        return True, '', {}

    def release_runtimes(self):
        """Release all the runtimes collected for the execution.

        """
        if not self._runtime_dependencies:
            return

        workbench = self.measure.plugin.workbench
        core = workbench.get_plugin('enaml.workbench.core')
        cmd = 'ecpy.app.dependencies.release_runtimes'
        core.invoke_command(cmd, dict(owner='ecpy.measure',
                                      dependencies=self._runtime_dependencies))

        self._runtime_dependencies = None

    def get_build_dependencies(self):
        """Get the build dependencies associated with the main task.

        Returns
        -------
        dependencies : BuildContainer
            BuildContainer as returned by 'ecpy.app.dependencies.collect'.
            The errors member should be checked to detect errors.

        """
        workbench = self.measure.plugin.workbench
        core = workbench.get_plugin('enaml.workbench.core')

        if not self._build_analysis:
            cmd = 'ecpy.app.dependencies.analyse'
            deps = core.invoke_command(cmd,
                                       {'obj': self.measure.root_task,
                                        'dependencies': ['build']})
            if deps.errors:
                return deps
            self._build_analysis = deps.dependencies

        if not self._build_dependencies:
            cmd = 'ecpy.app.dependencies.collect'
            deps = core.invoke_command(cmd,
                                       dict(dependencies=self._build_analysis,
                                            kind='build'))
            if not deps.errors:
                self._build_dependencies = deps

        else:
            deps = self._build_dependencies

        return deps

    def get_runtime_dependencies(self, id):
        """Access the runtime dependencies associated with a hook or the main
        task

        Parameters
        ----------
        id: unicode
            Id of the hook for which to retrieve the runtimes or 'main' for
            the main task.

        Returns
        -------
        dependencies : dict
            Dependencies for the requested measure component.

        Raises
        ------
        RuntimeError :
            Raised if this method is called before collect_runtimes.


        """
        if self._runtime_dependencies is None:
            raise RuntimeError('Runtime dependencies must be collected '
                               '(calling collect_runtimes) before they can be '
                               'queried.')

        valids = self._runtime_map.get(id)
        if not valids:
            return {}

        deps = self._runtime_dependencies
        queried = {}
        for runtime_id, r_deps in valids.iteritems():
            queried[runtime_id] = {k: deps[runtime_id][k] for k in r_deps}

        return queried

    def reset(self):
        """Cleanup all cached values.

        """
        if self._runtime_dependencies:
            raise RuntimeError('Cannot reset dependencies while holding '
                               'runtime dependencies')
        self._build_analysis.clear()
        self._build_dependencies = None
        self._runtime_analysis.clear()
        self._runtime_map.clear()

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Cached build dependencies analysis for the main task.
    #: No actual dependency is stored, this dict can be used to collect them
    _build_analysis = Dict()

    #: Cached build dependencies of the main task.
    #: Contains the actual dependencies.
    _build_dependencies = Value()

    #: Cached runtime dependencies analysis for the main task and the hooks.
    #: No actual dependency is stored, this dict can be used to collect them
    _runtime_analysis = Typed(defaultdict, (set,))

    #: Cached runtime dependencies of the main task and the hooks.
    #: Contains the actual dependencies.
    #: Set to None when dependencies have not been collected.
    _runtime_dependencies = Typed(dict)

    #: Mapping determining which component has which dependency.
    _runtime_map = Dict()

    def _update_runtime_analysis(self, new):
        """Update the known runtime dependencies.

        """
        analysis = self._runtime_analysis
        for k in new:
            analysis[k].update(new[k])


class Measure(HasPrefAtom):
    """Object representing all the aspects of a measure.

    """
    #: Name of the measure.
    name = Unicode().tag(pref=True)

    #: Id of that particular iteration of the measure. This value is used when
    #: saving the measure before running it. It is also communicated to the
    #: root task
    id = Unicode().tag(pref=True)

    #: Current measure status.
    status = Enum('READY', 'RUNNING', 'PAUSING', 'PAUSED', 'RESUMING',
                  'STOPPING', 'EDITING', 'SKIPPED', 'FAILED', 'COMPLETED',
                  'INTERRUPTED')

    #: Detailed information about the measure status.
    infos = Unicode()

    #: Path to the last file in which that measure was saved.
    path = Unicode()

    #: Root task holding the measure logic.
    root_task = Typed(RootTask)

    #: Dict of active monitor for this measure.
    monitors = Typed(OrderedDict, ())

    #: Dict of pre-measure execution routines.
    pre_hooks = Typed(OrderedDict, ())

    #: Dict of post-measure execution routines.
    post_hooks = Typed(OrderedDict, ())

    #: Reference to the measure plugin managing this measure.
    plugin = ForwardTyped(measure_plugin)

    #: Flag signaling whether the user chose to enqueue the measure knowing
    #: some tests are failing.
    forced_enqueued = Bool()

    #: Object handling the collection and access to the measure dependencies.
    dependencies = Typed(MeasureDependencies)

    #: Result object returned by the engine when the root_task has been
    #: executed. Can be used by post-execution hook to adapt their behavior.
    task_execution_result = Value()

    def __init__(self, **kwargs):

        super(Measure, self).__init__(**kwargs)
        self.add_tool('pre-hook', 'ecpy.internal_checks')

    def save(self, path):
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
    def load(cls, measure_plugin, path, build_dep=None):
        """Build a measure from a ConfigObj file.

        Parameters
        ----------
        measure_plugin : MeasurePlugin
            Instance of the MeasurePlugin storing all declarations.

        path : unicode
            Path of the file from which to load the measure.

        build_dep : dict, optional
            Build dependencies of the main task.

        Returns
        -------
        measure : Measure|None
            Measure buil from the config or None if and error occurred.

        errors : dict
            Dictionary describing the errors that occured.

        """
        # Create the measure.
        measure = cls(plugin=measure_plugin)
        config = ConfigObj(path)
        measure.path = path
        measure.update_members_from_preferences(config)

        # Return values storing the errors details.
        errors = defaultdict(dict)

        # Get the workbench and core plugin.
        workbench = measure_plugin.workbench
        core = workbench.get_plugin('enaml.workbench.core')

        # Load the task.
        cmd = 'ecpy.tasks.build_root'
        build_dep = build_dep if build_dep else workbench
        kwarg = {'mode': 'from config', 'config': config['root_task'],
                 'build_dep': build_dep}
        try:
            measure.root_task = core.invoke_command(cmd, kwarg, measure)
        except Exception:
            msg = 'Building %s, failed to restore task : %s'
            errors['main task'] = msg % (config.get('name'), format_exc())

        for kind in ('monitor', 'pre-hook', 'post-hook'):
            saved = config.get(kind.replace('-', '_')+'s', {})

            # Make sure we always have the internal pre-hook in the right
            # position.
            if kind == 'pre-hook':
                if 'ecpy.internal_checks' in saved:
                    del measure.pre_hooks['ecpy.internal_checks']

            for id, state in saved.iteritems():
                try:
                    obj = measure_plugin.create(kind, id, default=False)
                    obj.set_state(state)
                except Exception:
                    msg = 'Failed to restore {} {}: {}'.format(kind, id,
                                                               format_exc())
                    errors[kind][id] = msg
                    continue

                measure.add_tool(kind, id, obj)

        measure.name = config.get('name', '')

        if errors:
            measure = None

        return measure, errors

    def run_checks(self, **kwargs):
        """Run all measure checks.

        This is done at enqueueing time and before actually executing a measure
        save it it was forcibly enqueued. The dependencies needs to be
        collected before calling this method.

        Parameters
        ----------
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
        workbench = self.plugin.workbench

        self._write_infos_in_task()

        msg = 'Running checks for pre-measure hook %s for measure %s'
        for id, hook in self.pre_hooks.iteritems():
            logger.debug(msg, id, self.name)
            answer = hook.check(workbench, **kwargs)
            if answer is not None:
                check, errors = answer
                if errors:
                    full_report[id] = errors
                result = result and check

        msg = 'Running checks for post-measure hook %s for measure %s'
        for id, hook in self.post_hooks.iteritems():
            logger.debug(msg, id, self.name)
            answer = hook.check(workbench, **kwargs)
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
                                         monitor.handle_database_change):
                database.observe('notifier', monitor.handle_database_change)

    def enter_running_state(self):
        """Make the measure ready to run.

        """
        database = self.root_task.database
        for monitor in self.monitors.values():
            if database.has_observer('notifier',
                                     monitor.handle_database_change):
                database.unobserve('notifier', monitor.handle_database_change)

    def add_tool(self, kind, id, tool=None):
        """Add a tool to the measure.

        Newly added tools are always appended to the list of existing ones.

        Parameters
        ----------
        kind : {'monitor', 'pre-hook', 'post-hook'}
            Kind of tool being added to the measure.

        id : unicode
            Id of the tool being added.

        tool : MeasureTool, optional
            Tool being added, if not specified a new instance will be created.

        """
        if kind not in ('pre-hook', 'monitor', 'post-hook'):
            msg = ('Tool kind must be "pre-hook", "monitor" or "post-hook" '
                   'not %s')
            raise ValueError(msg % kind)

        if not tool:
            tool = self.plugin.create(kind, id)

        kind = kind.replace('-', '_') + 's'

        tools = getattr(self, kind).copy()

        if id in tools:
            msg = 'Tool %s is already present in measure %s'
            raise KeyError(msg % (id, self.name))

        tool.link_to_measure(self)

        tools[id] = tool
        setattr(self, kind, tools)

    def move_tool(self, kind, old, new):
        """Modify hooks execution order.

        Parameters
        ----------
        kind : {'pre-hook', 'post-hook'}
            Kind of hook to move.

        old : int
            Index at which the tool is currently.

        new_pos : int
            New index at which the tool should be.

        """
        if kind not in ('pre-hook', 'post-hook'):
            msg = ('Tool kind must be "pre-hook" or "post-hook" '
                   'not %s')
            raise ValueError(msg % kind)

        kind = kind.replace('-', '_') + 's'

        tools = getattr(self, kind)
        keys = list(tools.keys())
        id = keys[old]
        del keys[old]
        keys.insert(new, id)

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
        if kind not in ('pre-hook', 'monitor', 'post-hook'):
            msg = ('Tool kind must be "pre-hook", "monitor" or "post-hook" '
                   'not %s')
            raise ValueError(msg % kind)

        kind = kind.replace('-', '_') + 's'

        tools = getattr(self, kind).copy()

        if id not in tools:
            msg = 'Tool %s is not present in measure %s'
            raise KeyError(msg % (id, self.name))

        tools[id].unlink_from_measure()

        del tools[id]
        setattr(self, kind, tools)

    def collect_monitored_entries(self):
        """Get all the entries the monitors ask to be notified about.

        Returns
        -------
        entries : list
            List of the entries the engine will to observe.

        """
        entries = []
        for monitor in self.monitors.values():
            entries.extend(monitor.monitored_entries)

        return list(set(entries))

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Dictionary storing the collected runtime dependencies.
    _runtimes = Dict()

    def _write_infos_in_task(self):
        """Write all the measure values in the root_task database.

        """
        self.root_task.write_in_database('meas_name', self.name)
        self.root_task.write_in_database('meas_id', self.id)
        self.root_task.write_in_database('meas_date', text(date.today()))

    def _post_setattr_root_task(self, old, new):
        """Add the entries contributed by the measure to the task database.

        """
        entries = new.database_entries.copy()
        entries.update({'meas_name': self.name, 'meas_id': self.id,
                        'meas_date': ''})

    def _default_dependencies(self):
        """Default value for the dependencies member.

        """
        return MeasureDependencies(measure=self)
