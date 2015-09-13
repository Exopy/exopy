# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Object reponsible for a measure execution.

Please note that the 'real' work of performing the tasks is handled by the
engine. This object handles all the other aspects (running of the hooks,
handling of the monitors, ...)

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os
import logging
from time import sleep
from traceback import format_exc
from threading import Thread

import enaml
from atom.api import Atom, Typed, ForwardTyped, Value, Bool
from enaml.widgets.api import Window
from enaml.layout.api import InsertTab, FloatItem

from .engines import BaseEngine, ExecutionInfos
from .measure import Measure
from ..utils.bi_flag import BitFlag
with enaml.imports():
    from .workspace.monitors_window import MonitorsWindow

logger = logging.getLogger(__name__)


INVALID_MEASURE_STATUS = ['EDITING', 'SKIPPED', 'FAILED', 'COMPLETED',
                          'INTERRUPTED']


def plugin():
    """Delayed import to avoid circular references.

    """
    from .plugin import MeasurePlugin
    return MeasurePlugin


class MeasureProcessor(Atom):
    """Object reponsible for a measure execution.

    """
    #: Boolean indicating whether or not the processor is working.
    active = Bool()

    #: Reference to the measure plugin.
    plugin = ForwardTyped(plugin)

    #: Currently run measure or last measure run.
    running_measure = Typed(Measure)

    #: Instance of the currently used engine.
    engine = Typed(BaseEngine)

    #: Boolean indicating whether or not process all enqueued measures.
    continuous_processing = Bool(True)

    #: Monitors window
    monitors_window = Typed(Window)

    def start_measure(self, measure):
        """Start a new measure.

        """
        if self._thread and self._thread.is_alive():
            self._state.set('stop_processing')
            self._thread.join(5)
            if self._thread.is_alive():
                core = self.plugin.workbench.get_plugin('enaml.workbench.core')
                cmd = 'ecpy.app.errors.signal'
                msg = ("Can't stop the running execution thread. Please "
                       "restart the application and consider reporting this "
                       "as a bug.")
                core.invoke_command(cmd, dict(kind='error', message=msg))
                return

        if self.continuous_processing:
            self._state.set('continuous_processing')
        else:
            self._state.clear('continuous_processing')

        self.active = True
        self._thread = Thread(target=self._run_measures,
                              args=(measure,))
        self._thread.start()

    def pause_measure(self):
        """Pause the currently active measure.

        """
        logger.info('Pausing measure {}.'.format(self.running_measure.name))
        self.running_measure.status = 'PAUSING'
        self._state.set('pause_attempt')
        if self._state.test('running_main'):
            self._engine.pause()
            self._engine.observe('status', self._watch_engine_state)
        else:
            if self._active_hook:
                self._active_hook.pause()
                self._active_hook.observe('paused', self._watch_hook_state)

    def resume_measure(self):
        """Resume the currently paused measure.

        """
        logger.info('Resuming measure {}.'.format(self.running_measure.name))
        self.running_measure.status = 'RESUMING'
        self._state.clear('paused')
        self._state.set('resuming')
        if self._state.test('running_main'):
            self._engine.resume()
            self._engine.observe('status', self._watch_engine_state)
        else:
            if self._active_hook:
                self._active_hook.resume()
                self._active_hook.observe('resumed',
                                          self._watch_hook_state)

    def stop_measure(self, no_post_exec=False, force=False):
        """Stop the currently active measure.

        """
        logger.info('Stopping measure {}.'.format(self.running_measure.name))
        self._state.set('stop_attempt')
        self.running_measure.status = 'STOPPING'
        if no_post_exec or force:
            self._state.set('no_post_exec')

        if self._state.test('running_main'):
            self._engine.stop(force)
        else:
            if self._active_hook:
                self._active_hook.stop(force)

    def stop_processing(self, no_post_exec=False, force=False):
        """Stop processing the enqueued measure.

        """
        logger.info('Stopping measure {}.'.format(self.running_measure.name))
        self._state.set('stop_attempt', 'stop_processing')
        self._state.clear('processing')
        if no_post_exec or force:
            self._state.set('no_post_exec')
        if self._state.test('running_main'):
            self._engine.stop(force)
        else:
            if self._active_hook:
                self._active_hook.stop(force)

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Background thread handling the measure execution
    _thread = Value()

    #: Internal flags used to keep track of the execution state.
    _state = Typed(BitFlag,
                   ('processing', 'running_pre_hooks', 'running_main',
                    'running_post_hooks', 'pause_attempt', 'paused',
                    'resuming', 'stop_attempt', 'stop_processing',
                    'no_post_exec', 'continuous_processing')
                   )

    #: Hook currently executed. The value is meaningful only when
    #: 'running_pre_hooks' or 'running_post_hooks' is set.
    _active_hook = Value()

    def _run_measures(self, measure):
        """Run measures (either all enqueued or only one)

        This code is executed by a thread (stored in _thread)

        Parameters
        ----------
        measure : Measure
            First measure to run. Other measures will be run in their order of
            appearance in the queue if the user enable continuous processing.

        """
        # If the engine does not exist, create one.
        plugin = self.plugin
        if not self.engine:
            self.engine = plugin.create('engine', plugin.selected_engine)

        # Mark that we started processing measures.
        self._state.set('processing')

        # Process enqueued measure as long as we are supposed to.
        while not self._state.test('stop_processing'):

            # Clear the internal state to start fresh.
            self._clear_state()

            # If we were provided with a measure use it, otherwise find the
            # next one.
            if measure:
                meas = measure
                measure = None
            else:
                meas = self.find_next_measure()

            # If there is a measure register it as the running one, update its
            # status and log its execution.
            if meas is not None:

                meas_id = meas.name + '_' + meas.id
                enaml.application.deferred_call(setattr, self,
                                                'running_measure', meas)
                self._set_measure_state('RUNNING', 'The measure is being run.')

                msg = 'Starting execution of measure %s'
                logger.info(msg % meas.name + meas.id)

                status, infos = self._run_measure(meas)
                # Release runtime dependencies.
                meas.dependencies.release_runtimes()

            # If no measure remains stop.
            else:
                break

            # Log the result.
            mess = 'Measure %s processed, status : %s' % (meas_id, status)
            if infos:
                mess += '\n' + infos
            logger.info(mess)

            # Update the status and infos.
            self._set_measure_state(status, infos)

            # If we are supposed to stop, stop.
            if not self._state.test('continuous_processing'):
                break

        if self.engine and self.plugin.engine_policy == 'stop':
            self._stop_engine()

        self._state.clear('processing')
        enaml.application.deferred_call(setattr, (self, 'active', False))

    def _run_measure(self, measure):
        """Run a single measure.

        """
        # Switch to running state.
        measure.enter_running_state()

        meas_id = measure.name + '_' + measure.id

        # Collect runtime dependencies
        res, msg, errors = measure.dependencies.collect_runtimes()
        if not res:
            status = 'SKIPPED' if 'unavailable' in msg else 'FAILED'
            return status, msg + '\n' + errors_to_msg(errors)

        # Records that we got access to all the runtimes.
        mess = ('The use of all runtime resources have been granted to the '
                'measure %s' % meas_id)
        logger.info(mess.replace('\n', ' '))

        # Run checks now that we have all the runtimes.
        res, errors = measure.run_checks(self.workbench)
        if not res:
            msg = 'Measure %s failed to pass the checks :\n' % meas_id
            return 'FAILED', msg + errors_to_msg(errors)

        # Now that we know the measure is going to run save it.
        default_filename = meas_id + '.meas.ini'
        path = os.path.join(measure.root_task.default_path, default_filename)
        measure.save(path)

        logger.info('Starting measure {}.'.format(meas_id))

        # Execute all pre-execution hooks.
        result, errors = self._run_pre_execution()
        if not result:
            msg = 'Measure %s failed to run pre-execution hooks :\n' % meas_id
            return 'FAILED', msg + errors_to_msg(errors)

        result = True
        errors = {}
        if self._check_for_pause_or_stop():

            # Connect new monitors, and start them.
            self._start_monitors()

            # Assemble the task infos for the engine to run the main task.
            deps = measure.dependencies
            infos = ExecutionInfos(
                id=meas_id+'.main',
                task=measure.root_task,
                build_deps=deps.get_build_dependencies(),
                runtime_deps=deps.get_runtime_dependencies('main'),
                database_entries=measure.collect_entries_to_observe(),
                )

            # Ask the engine to perform the main task.
            self._state.set('running_main')
            execution_result = self.engine.perform(infos)
            self._state.clear('running_main')

            # Record the result and store engine return value in the measure
            # for the post execution hooks.
            result &= execution_result.success
            errors.update(execution_result.errors)
            measure.task_execution_result = execution_result

            # Disconnect monitors.
            self._stop_monitors()

        # Execute all post-execution hooks if pertinent.
        if not self._state.test('no_post_exec'):
            result, errors = self._run_pre_execution()

        if not result:
            if not execution_result.success:
                msg = 'Execution of the main task failed :\n'
            else:
                msg = 'Some post-execution hook failed to run :\n'

            return 'FAILED', msg + errors_to_msg(errors)

        return 'COMPLETED', 'The measure successfully completed.'

    def _run_pre_execution(self, measure):
        """Run pre measure execution operations.

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

        self._state.set('running_pre_hooks')
        meas_id = measure.name + '_' + measure.id

        for id, hook in self.pre_hooks.iteritems():
            if not self._check_for_pause_or_stop():
                break
            logger.debug('Calling pre-measure hook %s for measure %s',
                         id, meas_id)
            with self._lock:
                self._active_hook = hook

            try:
                hook.run(self.plugin.workbench, measure, self.engine)
            except Exception:
                result = False
                full_report[id] = format_exc()

            # Prevent issues with pausing/resuming
            with self._lock:
                self._active_hook = None

        self._state.clear('running_pre_hooks')

        return result, full_report

    def _run_post_execution(self, measure):
        """Run post measure operations.

        Parameters
        ----------
        measure : Measure


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

        self._state.set('running_post_hooks')
        meas_id = measure.name + '_' + measure.id

        for id, hook in self.pre_hooks.iteritems():
            if not self._check_for_pause_or_stop():
                break
            logger.debug('Calling post-measure hook %s for measure %s',
                         id, meas_id)
            with self._lock:
                self._active_hook = hook

            try:
                hook.run(self.plugin.workbench, measure, self.engine)
            except Exception:
                result = False
                full_report[id] = format_exc()

            # Prevent issues with pausing/resuming
            with self._lock:
                self._active_hook = None

        self._state.clear('running_post_hooks')

        return result, full_report

    def _start_monitors(self, measure):
        """Start the monitors attached to a measure and display them.

        If no dedicated window exists one will be created. For monitors for
        which a dockitem already exists it is re-used.

        """
        def start_monitors(self, measure):

            workbench = self.plugin.workbench
            if not self.monitors_window:
                ui_plugin = workbench.get_plugin('enaml.workbench.ui')
                self.monitors_window = MonitorsWindow(ui_plugin.window)

            self.monitors_window.measure = measure

            dock_area = self.monitors_window.dock_area
            anchor = ''
            for dock_item in dock_area.dock_items():
                if dock_item.name not in measure.monitors:
                    dock_item.destroy()
                elif not anchor:
                    anchor = dock_item.name

            ops = []
            for monitor in measure.monitors.values():
                decl = monitor.declaration
                dock_item = dock_area.find(decl.id)
                if dock_item is None:
                    try:
                        dock_item = decl.create_item(workbench, dock_area)
                        if dock_item.float_default:
                            ops.append(FloatItem(item=decl.id))
                        else:
                            ops.append(InsertTab(item=decl.id, target=anchor))
                    except Exception:
                        logger.error('Failed to create widget for monitor %s',
                                     id)
                        logger.debug(format_exc())
                        continue

                self.engine.observe('news', monitor.process_news)
                dock_item.monitor = monitor
                monitor.start()

            dock_area.update_layout(ops)

            if self.plugin.auto_show_monitors:
                self.monitors_window.show()

        # Executed in the main thread to avoid GUI update issues.
        sheduled = enaml.application.schedule(start_monitors, (self, measure),
                                              priority=100)
        while sheduled.pending():
            sleep(0.05)

    def _stop_monitors(self, measure):
        """Disconnect the monitors from the engine and stop them.

        The monitors windows is not hidden as the user may want to check it
        later.

        """
        def stop_monitors(self, measure):
            engine = self._engine
            if engine:
                engine.unobserve('news')
            for monitor in measure.monitors.values():
                monitor.stop()

        # Executed in the main thread to avoid GUI update issues.
        sheduled = enaml.application.schedule(stop_monitors, (measure),
                                              priority=100)
        while sheduled.pending():
            sleep(0.01)

    def _find_next_measure(self):
        """Find the next runnable measure in the queue.

        Returns
        -------
        measure : Measure
            First valid measurement in the queue or None if there is no
            available measure.

        """
        enqueued_measures = self.plugin.enqueued_measures.measures
        i = 0
        measure = None
        # Look for a measure not being currently edited. (Can happen if the
        # user is editing the second measure when the first measure ends).
        while i < len(enqueued_measures):
            measure = enqueued_measures[i]
            if measure.status in INVALID_MEASURE_STATUS:
                i += 1
                measure = None
            else:
                break

        return measure

    def _check_for_pause_or_stop(self):
        """Check if a pause or stop request is pending and process it.

        Returns
        -------
        should_stop : bool
            Booelan indicating whether or not the execution of the measure
            should stop.

        """
        flag = self._state

        if flag.test('stop_attempt'):
            return False

        if flag.test('pause_attempt'):
            flag.set('paused')
            flag.clear('pause_attempt')
            self._set_measure_state('PAUSED', 'The measure is paused.')

            if (flag.test('running_pre_hooks') or
                    flag.test('running_post_hooks')):
                self._active_hook.unobserve('paused', self._watch_hook_state)

            while True:
                if flag.wait(1, 'resuming'):
                    flag.clear('resuming')
                    self._set_measure_state('RUNNING',
                                            'The measure has resumed.')
                    return True

                if flag.test('stop_attempt'):
                    return False

        return True

    # Those must post update of measure.status and remove observers
    def _watch_engine_state(self, change):
        """Observe engine state to notify that the engine paused or resumed.

        """
        if change['value'] == 'Paused':
            self._state.set('paused')
            self._state.clear('pause_attempt')
            self._engine.unobserve('status', self._watch_engine_state)
            self._set_measure_state('PAUSED', 'The measure is paused.')

        elif change['value'] == 'Running':
            self._state.clear('resuming')
            self._engine.unobserve('status', self._watch_engine_state)
            self._set_measure_state('RUNNING', 'The measure has resumed.')

    def _watch_hook_state(self, change):
        """Observe hook paused/resumed events to validate pausing/resuming.

        """
        if change['name'] == 'paused':
            self._state.set('paused')
            self._state.clear('pause_attempt')
            self._engine.unobserve('status', self._watch_engine_state)
            self._set_measure_state('PAUSED', 'The measure is paused.')

        elif change['name'] == 'resumed':
            self._state.clear('resuming')
            self._engine.unobserve('status', self._watch_engine_state)
            self._set_measure_state('RUNNING', 'The measure has resumed.')

    def _set_measure_state(self, status, infos):
        """Set the measure status and infos in the main thread.

        """
        measure = self.running_measure
        enaml.application.deferred_call(setattr, measure, 'status', status)
        enaml.application.deferred_call(setattr, measure, 'infos', infos)

    def _stop_engine(self):
        """Stop the engine.

        """
        engine = self._engine
        self.stop_processing()
        i = 0
        while engine and engine.active:
            sleep(0.5)
            i += 1
            if i > 10:
                self.force_stop_processing()

    def _clear_state(self):
        """Clear the state when starting while preserving persistent settings.

        """
        flags = list(self._state.flags)
        flags.remove('processing')
        flags.remove('continuous_processing')
        self._state.clear(self._state.flages)

    def _post_setattr_continuous_processing(self, old, new):
        """Make sure the internal bit flag does reflect the real setting.

        """
        if new:
            self._state.clear('continuous_processing')
        else:
            self._state.set('continuous_processing')


def errors_to_msg(errors):
    """Convert a dictionary of errors in a well formatted message.

    """
    err = '\n'.join(('- %s : %s' % (k, v) for k, v in errors.items()))
    return 'The following errors occured :\n' + err