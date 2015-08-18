# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Workspace used for editing and executing measures.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

# XXXXX
import logging
import os
import enaml
from atom.api import Typed, Value, set_default
from enaml.application import deferred_call
from enaml.workbench.ui.api import Workspace
from enaml.widgets.api import FileDialogEx
from inspect import cleandoc
from textwrap import fill

from .measure import Measure
from .plugin import MeasurePlugin

from ..tasks.api import RootTask

with enaml.imports():
    from enaml.stdlib.message_box import question
    from .checks.checks_display import ChecksDisplay
    from .engines.selection import EngineSelector
    from .content import MeasureContent, MeasureSpaceMenu


# ID used when adding handler to the logger.
LOG_ID = 'ecpy.measure.workspace'

logger = logging.getLogger(__name__)


class MeasureSpace(Workspace):
    """Workspace dedicated tot measure edition and execution.

    """
    #: Reference to the plugin to which the workspace is linked.
    plugin = Typed(MeasurePlugin)

    # Reference to the log panel model received from the log plugin.
    log_model = Value()

    window_title = set_default('Measure')

    def start(self):
        """Start the workspace, create a blanck measure if necessary and
        get engine contribution.

        """
        # Add a reference to thet workspace in the plugin and keep a reference
        # to the plugin.
        plugin = self.workbench.get_plugin('ecpy.measure')
        plugin.workspace = self
        self.plugin = plugin

        # Add handler to the root logger to display messages in panel.
        core = self.workbench.get_plugin('enaml.workbench.core')
        cmd = 'ecpy.app.logging.add_handler'
        self.log_model = core.invoke_command(cmd,
                                             {'id': LOG_ID, 'mode': 'ui'},
                                             self)[0]

        # Check whether or not a measure is already being edited.
        if not plugin.edited_measures:
            self._new_measure()

        # Create content.
        self.content = MeasureContent(workspace=self)

        # Contribute menus.
        self.workbench.register(MeasureSpaceMenu())

        # Check whether or not an engine can contribute.
        if plugin.selected_engine:
            engine = plugin._engines.contributions[plugin.selected_engine]
            deferred_call(engine.contribute_workspace, self)

        plugin.observe('selected_engine', self._update_engine_contribution)

    def stop(self):
        """Stop the workspace and clean.

        """
        plugin = self.plugin

        # Close all remaining monitor if any.
        if plugin.running_measure:
            for monitor in plugin.running_measure.monitors.values():
                monitor.stop()

        plugin.unobserve('selected_engine', self._update_engine_contribution)

        if plugin.selected_engine:
            engine = plugin._engines.contributions[plugin.selected_engine]
            engine.clean_workspace(self)

        # Remove handler from the root logger.
        core = self.workbench.get_plugin('enaml.workbench.core')
        cmd = 'ecpy.app.logging.remove_handler'
        core.invoke_command(cmd, {'id': LOG_ID}, self)

        self.workbench.unregister('ecpy.measure.workspace.menus')

        self.plugin.workspace = None

    # XXXX
    def new_measure(self):
        """
        """
        message = cleandoc("""The measurement you are editing is about to
                        be destroyed to create a new one. Press OK to
                        confirm, or Cancel to go back to editing and get a
                        chance to save it.""")

        result = question(self.content,
                          'Old measurement suppression',
                          fill(message.replace('\n', ' '), 79),
                          )

        if result is not None and result.action == 'accept':
            self._new_measure()

    def save_measure(self, measure, auto=True):
        """ Save a measure in a file.

        Parameters
        ----------
        measure : Measure
            Measure to save.

        auto : bool, optional
            When true if a path is associated to the measure save it there,
            otherwise ask the user where to save it.

        """
        if not auto or not measure.path:
            get_file = FileDialogEx.get_save_file_name
            path = measure.path or self.plugin.path
            full_path = get_file(parent=self.content,
                                 current_path=path,
                                 name_filters=[u'*.meas.ini'])
            if not full_path:
                return
            elif not full_path.endswith('.meas.ini'):
                full_path += '.meas.ini'

        else:
            full_path = measure.path

        measure.save_measure(full_path)

    # XXXX
    def load_measure(self, mode):
        """ Load a measure.

        Parameters
        ----------
        mode : str
            file: ask the user to specify a file from which to load a measure.
            template: ask the user to choose a template and use default for the
                rest.

        """
        if mode == 'file':
            get_file = FileDialogEx.get_open_file_name
            full_path = get_file(name_filters=[u'*.ini'],
                                 current_path=self.plugin.paths.get('measure',
                                                                    ''))
            if not full_path:
                return

            self.plugin.edited_measure = Measure.load_measure(self.plugin,
                                                              full_path)
            self.plugin.edited_measure_path = full_path
            self.plugin.paths['measure'] = os.path.dirname(full_path)

        elif mode == 'template':
            # TODO create brand new measure using defaults from plugin and
            # load template
            pass

    # XXXX
    def enqueue_measure(self, measure):
        """Put a measure in the queue if it pass the tests.

        First the check method of the measure is called. If the tests pass,
        the measure is enqueued and finally saved in the default folder
        ('default_path' attribute of the `RootTask` describing the measure).
        Otherwise the list of the failed tests is displayed to the user.

        Parameters
        ----------
        measure : instance(`Measure`)
            Instance of `Measure` representing the measure.

        Returns
        -------
        bool :
            True is the measure was successfully enqueued, False otherwise.

        """
        logger = logging.getLogger(__name__)

        # First of all build the runtime dependencies
        core = self.workbench.get_plugin('enaml.workbench.core')
        cmd = u'hqc_meas.dependencies.collect_dependencies'
        res = core.invoke_command(cmd, {'obj': measure.root_task},
                                  self.plugin)
        if not res[0]:
            for id in res[1]:
                logger.warn(res[1][id])
            return False

        build_deps = res[1]
        runtime_deps = res[2]

        use_instrs = 'profiles' in runtime_deps
        test_instrs = use_instrs and runtime_deps['profiles']
        if use_instrs and not test_instrs:
            mes = cleandoc('''The profiles requested for the measurement {} are
                           not available, instr tests will be skipped and
                           performed before actually starting the
                           measure.'''.format(measure.name))
            logger.info(mes.replace('\n', ' '))

        measure.root_task.run_time = runtime_deps.copy()

        check, errors = measure.run_checks(self.workbench,
                                           test_instr=test_instrs)

        measure.root_task.run_time.clear()

        if use_instrs:
            profs = runtime_deps.pop('profiles').keys()
            core.invoke_command(u'hqc_meas.instr_manager.profiles_released',
                                {'profiles': profs}, self.plugin)

        if check:
            # If check is ok but there are some errors, those are warnings
            # which the user can either ignore and enqueue the measure, or he
            # can cancel the enqueuing and try again.
            if errors:
                dial = ChecksDisplay(errors=errors, is_warning=True)
                dial.exec_()
                if not dial.result:
                    return
            default_filename = measure.name + '_last_run.ini'
            path = os.path.join(measure.root_task.default_path,
                                default_filename)
            measure.save_measure(path)
            meas = Measure.load_measure(self.plugin, path, build_deps)
            # Here don't keep the profiles in the runtime as it will defeat the
            # purpose of the manager.
            meas.root_task.run_time = runtime_deps
            # Keep only a list of profiles to request (avoid to re-walk)
            if use_instrs:
                meas.store['profiles'] = profs
            meas.store['build_deps'] = build_deps
            meas.status = 'READY'
            meas.infos = 'The measure is ready to be performed by an engine.'
            self.plugin.enqueued_measures.append(meas)

            return True

        else:
            ChecksDisplay(errors=errors).exec_()
            return False

    # XXXX
    def reenqueue_measure(self, measure):
        """ Mark a measure already in queue as fitted to be executed.

        This method can be used to re-enqueue a measure that previously failed,
        for example becuse a profile was missing, the measure can then be
        edited again and will be executed in its turn.

        Parameters
        ----------
        measure : Measure
            The measure to re-enqueue

        """
        measure.enter_edition_state()
        measure.status = 'READY'
        measure.infos = 'Measure re-enqueued by the user'

    # XXXX
    def remove_processed_measures(self):
        """ Remove all the measures which have been processed from the queue.

        This method rely on the status of the measure. Only measures whose
        status is 'READY' will be left in the queue.

        """
        for measure in self.plugin.enqueued_measures[:]:
            if measure.status != 'READY':
                self.plugin.enqueued_measures.remove(measure)

    # XXXX
    def start_processing_measures(self):
        """ Starts to perform the measurement in the queue.

        Measure will be processed in their order of appearance in the queue.

        """
        logger = logging.getLogger(__name__)
        if not self.plugin.selected_engine:
            dial = EngineSelector(plugin=self.plugin)
            dial.exec_()
            if dial.selected_id:
                self.plugin.selected_engine = dial.selected_id
            else:
                msg = cleandoc('''The user did not select an engine to run the
                               measure''')
                logger.warn(msg)
                return

        self.plugin.flags = []

        measure = self.plugin.find_next_measure()
        if measure is not None:
            self.plugin.start_measure(measure)
        else:
            msg = cleandoc('''No curently enqueued measure can be run.''')
            logger.info(msg)

    # XXXX There should be a way for the user to know whether or not it the case
    def process_single_measure(self, measure):
        """ Performs a single measurement and then stops.

        Parameters
        ----------
        measure : Measure
            Measure to perform.

        """
        self.plugin.flags = []
        self.plugin.flags.append('stop_processing')

        self.plugin.start_measure(measure)

    def pause_current_measure(self):
        """Pause the currently active measure.

        """
        self.plugin.pause_measure()

    def resume_current_measure(self):
        """Resume the currently paused measure.

        """
        self.plugin.resume_measure()

    def stop_current_measure(self, no_post_exec=False):
        """Stop the execution of the currently executed measure.

        """
        self.plugin.stop_measure(no_post_exec)

    def stop_processing_measures(self, no_post_exec=False):
        """Stop processing enqueued measure.

        """
        self.plugin.stop_processing(no_post_exec)

    def force_stop_measure(self):
        """Force the measure to stop.

        """
        self.plugin.force_stop_measure()

    def force_stop_processing(self):
        """Force the measure to stop, and don't go on processing enqueued
        measures

        """
        self.plugin.force_stop_processing()

    # XXXX keep ?
    @property
    def dock_area(self):
        """ Getter for the dock_area of the content.

        """
        if self.content and self.content.children:
            return self.content.children[0]

    # --- Private API ---------------------------------------------------------

    def _new_measure(self):
        """ Create a new measure using the default tools.

        """
        measure = Measure(plugin=self.plugin)
        measure.root_task = RootTask()

        for pre_id in self.plugin.default_pre_hooks:
            if pre_id in self.plugin.pre_hooks:
                measure.add_tool('pre_hook', pre_id)
            else:
                msg = "Default pre-execution hook {} not found"
                logger.warn(msg.format(pre_id))

        for monitor_id in self.plugin.default_monitors:
            if monitor_id in self.plugin.monitors:
                measure.add_tool('monitor', monitor_id)
            else:
                msg = "Default monitor {} not found."
                logger.warn(msg.format(monitor_id))

        for post_id in self.plugin.default_post_hooks:
            if post_id in self.plugin.post_hooks:
                measure.add_tool('post_hook', post_id)
            else:
                msg = "Default post-execution hook {} not found"
                logger.warn(msg.format(post_id))

        # XXXX does not apply anymore as we can have multiple measures....
        self.plugin.edited_measure = measure

    def _add_edited_measure(self, measure):
        """
        """
        pass

    def _update_engine_contribution(self, change):
        """Make sure that the engine contribution to the workspace does reflect
        the currently selected engine.

        """
        if 'oldvalue' in change:
            old = change['oldvalue']
            if old in self.plugin.engines:
                engine = self.plugin._engines.contributions[old]
                engine.clean_workspace(self)

        new = change['value']
        if new and new in self.plugin.engines:
            engine = self.plugin._engines.contributions[new]
            engine.clean_workspace(self)
