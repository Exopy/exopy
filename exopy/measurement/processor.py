# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Object reponsible for a measurement execution.

Please note that the 'real' work of performing the tasks is handled by the
engine. This object handles all the other aspects (running of the hooks,
handling of the monitors, ...)

"""
import os
import logging
from time import sleep
from threading import Thread, RLock

import enaml
from atom.api import Atom, Typed, ForwardTyped, Value, Bool
from enaml.widgets.api import Window
from enaml.layout.api import InsertTab, FloatItem
from enaml.application import deferred_call, schedule

from .engines.api import BaseEngine, ExecutionInfos
from .measurement import Measurement
from ..utils.flags import BitFlag
from ..utils.traceback import format_exc


logger = logging.getLogger(__name__)


def plugin():
    """Delayed import to avoid circular references.

    """
    from .plugin import MeasurementPlugin
    return MeasurementPlugin


def schedule_and_block(func, args=(), kwargs={}, priority=100):
    """Schedule a function call on the main thread and wait for it to complete.

    """
    sheduled = schedule(func, args, kwargs, priority=100)
    while sheduled.pending():
        sleep(0.05)


class MeasurementProcessor(Atom):
    """Object reponsible for a measurement execution.

    """
    #: Boolean indicating whether or not the processor is working.
    active = Bool()

    #: Reference to the measurement plugin.
    plugin = ForwardTyped(plugin)

    #: Currently run measurement or last measurement run.
    running_measurement = Typed(Measurement)

    #: Instance of the currently used engine.
    engine = Typed(BaseEngine)

    #: Boolean indicating whether or not process all enqueued measurements.
    continuous_processing = Bool(True)

    #: Monitors window
    monitors_window = Typed(Window)

    def start_measurement(self, measurement):
        """Start a new measurement.

        """
        if self._thread and self._thread.is_alive():
            self._state.set('stop_processing')
            self._thread.join(5)
            if self._thread.is_alive():
                core = self.plugin.workbench.get_plugin('enaml.workbench.core')
                cmd = 'exopy.app.errors.signal'
                msg = ("Can't stop the running execution thread. Please "
                       "restart the application and consider reporting this "
                       "as a bug.")
                core.invoke_command(cmd, dict(kind='error', message=msg))
                return

        if self.continuous_processing:
            self._state.set('continuous_processing')
        else:
            self._state.clear('continuous_processing')

        deferred_call(setattr, self, 'active', True)
        self._thread = Thread(target=self._run_measurements,
                              args=(measurement,))
        self._thread.daemon = True
        self._thread.start()

    def pause_measurement(self):
        """Pause the currently active measurement.

        """
        logger.info('Pausing measurement %s.', self.running_measurement.name)
        self.running_measurement.status = 'PAUSING'
        self._state.set('pause_attempt')
        if self._state.test('running_main'):
            self.engine.pause()
            self.engine.observe('status', self._watch_engine_state)
        else:
            if self._active_hook:
                self._active_hook.pause()
                self._active_hook.observe('paused', self._watch_hook_state)

    def resume_measurement(self):
        """Resume the currently paused measurement.

        """
        logger.info('Resuming measurement %s.', self.running_measurement.name)
        self.running_measurement.status = 'RESUMING'
        self._state.clear('paused')
        self._state.set('resuming')
        if self._state.test('running_main'):
            self.engine.resume()
            self.engine.observe('status', self._watch_engine_state)
        else:
            if self._active_hook:
                self._active_hook.resume()
                self._active_hook.observe('resumed',
                                          self._watch_hook_state)

    def stop_measurement(self, no_post_exec=False, force=False):
        """Stop the currently active measurement.

        """
        if no_post_exec or force:
            self._state.set('no_post_exec')

        self._state.set('stop_attempt')
        if self.running_measurement:
            logger.info('Stopping measurement %s.',
                        self.running_measurement.name)
            self.running_measurement.status = 'STOPPING'

        if self._state.test('running_main'):
            self.engine.stop(force)
        else:
            if self._active_hook:
                self._active_hook.stop(force)

    def stop_processing(self, no_post_exec=False, force=False):
        """Stop processing the enqueued measurements.

        """
        if self.running_measurement:
            logger.info('Stopping measurement %s.',
                        self.running_measurement.name)
        if no_post_exec or force:
            self._state.set('no_post_exec')
        self._state.set('stop_attempt', 'stop_processing')
        self._state.clear('processing')
        if self._state.test('running_main'):
            self.engine.stop(force)
        else:
            if self._active_hook:
                self._active_hook.stop(force)

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Background thread handling the measurement execution
    _thread = Value()

    #: Internal flags used to keep track of the execution state.
    _state = Typed(BitFlag,
                   (('processing', 'running_pre_hooks', 'running_main',
                     'running_post_hooks', 'pause_attempt', 'paused',
                     'resuming', 'stop_attempt', 'stop_processing',
                     'no_post_exec', 'continuous_processing'),)
                   )

    #: Hook currently executed. The value is meaningful only when
    #: 'running_pre_hooks' or 'running_post_hooks' is set.
    _active_hook = Value()

    #: Lock to avoid race condition when pausing.
    _lock = Value(factory=RLock)

    def _run_measurements(self, measurement):
        """Run measurements (either all enqueued or only one)

        This code is executed by a thread (stored in _thread)

        Parameters
        ----------
        measurement : Measurement
            First measurement to run. Other measurements will be run in their
            order of appearance in the queue if the user enable continuous
            processing.

        """
        # If the engine does not exist, create one.
        plugin = self.plugin
        if not self.engine:
            engine = plugin.create('engine', plugin.selected_engine)
            schedule_and_block(setattr, (self, 'engine', engine))

        # Mark that we started processing measurements.
        self._state.set('processing')

        # Process enqueued measurement as long as we are supposed to.
        while not self._state.test('stop_processing'):

            # Clear the internal state to start fresh.
            self._clear_state()

            # If we were provided with a measurement use it, otherwise find the
            # next one.
            if measurement:
                meas = measurement
                measurement = None
            else:
                meas = self.plugin.find_next_measurement()

            # If there is a measurement register it as the running one, update
            # its status and log its execution.
            if meas is not None:

                meas_id = meas.name + '_' + meas.id
                self._set_measurement_state('RUNNING',
                                            'The measurement is being run.',
                                            meas)

                msg = 'Starting execution of measurement %s'
                logger.info(msg % meas.name + meas.id)

                status, infos = self._run_measurement(meas)
                # Release runtime dependencies.
                meas.dependencies.release_runtimes()

            # If no measurement remains stop.
            else:
                break

            # Log the result.
            mess = 'Measurement %s processed, status : %s' % (meas_id, status)
            if infos:
                mess += '\n' + infos
            logger.info(mess)

            # Update the status and infos.
            self._set_measurement_state(status, infos, clear=True)

            # If we are supposed to stop, stop.
            if (not self._state.test('continuous_processing') or
                    self._state.test('stop_processing')):
                break

        if self.engine and self.plugin.engine_policy == 'stop':
            self._stop_engine()

        self._state.clear('processing')
        deferred_call(setattr, self, 'active', False)

    def _run_measurement(self, measurement, headless=False):
        """Run a single measurement.

        """
        plugin = self.plugin
        if not self.engine:
            engine = plugin.create('engine', plugin.selected_engine)
            self.engine = engine

        # Switch to running state.
        measurement.enter_running_state()

        meas_id = measurement.name + '_' + measurement.id

        # Collect runtime dependencies
        res, msg, errors = measurement.dependencies.collect_runtimes()
        if not res:
            status = 'SKIPPED' if 'unavailable' in msg else 'FAILED'
            return status, msg + '\n' + errors_to_msg(errors)

        # Records that we got access to all the runtimes.
        mess = ('The use of all runtime resources have been granted to the '
                'measurement %s' % meas_id)
        logger.info(mess.replace('\n', ' '))

        # Run checks now that we have all the runtimes.
        if not measurement.forced_enqueued:
            res, errors = measurement.run_checks()
            if not res:
                msg = 'Measurement %s failed to pass the checks :\n' % meas_id
                return 'FAILED', msg + errors_to_msg(errors)

        # Now that we know the measurement is going to run save it.
        default_filename = meas_id + '.meas.ini'
        path = os.path.join(measurement.root_task.default_path,
                            default_filename)
        measurement.save(path)

        logger.info('Starting measurement {}.'.format(meas_id))

        # Execute all pre-execution hooks.
        result, errors = self._run_pre_execution(measurement)
        if not result:
            msg = ('Measurement %s failed to run pre-execution hooks :\n' %
                   meas_id)
            return 'FAILED', msg + errors_to_msg(errors)

        result = True
        errors = {}
        if self._check_for_pause_or_stop():
            if not headless:
                # Connect new monitors, and start them.
                logger.debug('Connecting monitors for measurement %s',
                             meas_id)
                self._start_monitors(measurement)

            # Assemble the task infos for the engine to run the main task.
            deps = measurement.dependencies
            infos = ExecutionInfos(
                id=meas_id+'-main',
                task=measurement.root_task,
                build_deps=deps.get_build_dependencies().dependencies,
                runtime_deps=deps.get_runtime_dependencies('main'),
                observed_entries=measurement.collect_monitored_entries(),
                checks=not measurement.forced_enqueued,
                )

            # Ask the engine to perform the main task.
            logger.debug('Passing measurement %s to the engine.',
                         meas_id)
            self._state.set('running_main')
            execution_result = self.engine.perform(infos)
            self._state.clear('running_main')

            # Record the result and store engine return value in the
            # measurement for the post execution hooks.
            result &= execution_result.success
            errors.update(execution_result.errors)
            measurement.task_execution_result = execution_result

            if not headless:
                # Disconnect monitors.
                logger.debug('Disonnecting monitors for measurement %s',
                             meas_id)
                self._stop_monitors(measurement)

        # Save the stop_attempt state to allow to run post execution if we
        # are supposed to do so.
        state = self._state.test('stop_attempt')
        self._state.clear('stop_attempt')

        # Execute all post-execution hooks if pertinent.
        if not self._state.test('no_post_exec'):
            res, errors = self._run_post_execution(measurement)
            result &= res

        if state:
            self._state.set('stop_attempt')

        if self._state.test('stop_attempt'):
            return ('INTERRUPTED',
                    'The measurement has been interrupted by the user.')

        if not result:
            if not execution_result.success:
                msg = 'Execution of the main task failed :\n'
            else:
                msg = 'Some post-execution hook failed to run :\n'

            return 'FAILED', msg + errors_to_msg(errors)

        return 'COMPLETED', 'The measurement successfully completed.'

    def _run_pre_execution(self, measurement):
        """Run pre measurement execution operations.

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
        meas_id = measurement.name + '_' + measurement.id

        for id, hook in measurement.pre_hooks.items():
            if not self._check_for_pause_or_stop():
                break
            logger.debug('Calling pre-measurement hook %s for measurement %s',
                         id, meas_id)
            with self._lock:
                self._active_hook = hook

            try:
                hook.run(self.plugin.workbench, self.engine)
            except Exception:
                result = False
                full_report[id] = format_exc()

            # Prevent issues with pausing/resuming
            with self._lock:
                self._active_hook.unobserve('paused', self._watch_hook_state)
                self._active_hook = None

        self._state.clear('running_pre_hooks')

        return result, full_report

    def _run_post_execution(self, measurement):
        """Run post measurement operations.

        Parameters
        ----------
        measurement : Measurement


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
        meas_id = measurement.name + '_' + measurement.id

        for id, hook in measurement.post_hooks.items():
            if not self._check_for_pause_or_stop():
                break
            logger.debug('Calling post-measurement hook %s for measurement %s',
                         id, meas_id)
            with self._lock:
                self._active_hook = hook

            try:
                hook.run(self.plugin.workbench, self.engine)
            except Exception:
                result = False
                full_report[id] = format_exc()

            # Prevent issues with pausing/resuming
            with self._lock:
                self._active_hook.unobserve('paused', self._watch_hook_state)
                self._active_hook = None

        self._state.clear('running_post_hooks')

        return result, full_report

    def _start_monitors(self, measurement):
        """Start the monitors attached to a measurement and display them.

        If no dedicated window exists one will be created. For monitors for
        which a dockitem already exists it is re-used.

        """
        def start_monitors(self, measurement):
            """Start the monitors attached to a measurement.

            Called in the main thread.

            """
            workbench = self.plugin.workbench
            if not self.monitors_window:
                with enaml.imports():
                    from .workspace.monitors_window import MonitorsWindow
                self.monitors_window = MonitorsWindow()
            else:
                self.monitors_window.send_to_front()

            self.monitors_window.measurement = measurement

            dock_area = self.monitors_window.dock_area
            anchor = ''
            for dock_item in dock_area.dock_items():
                if dock_item.name not in measurement.monitors:
                    dock_item.destroy()
                elif not anchor:
                    anchor = dock_item.name

            # We show the window now because otherwise the layout ops are not
            # properly executed.
            if self.plugin.auto_show_monitors:
                self.monitors_window.show()

            ops = []
            for monitor in measurement.monitors.values():
                decl = monitor.declaration
                dock_item = dock_area.find(decl.id)
                if dock_item is None:
                    try:
                        dock_item = decl.create_item(workbench, dock_area)
                    except Exception:
                        msg = 'Failed to create widget for monitor %s :\n %s'
                        logger.error(msg, decl.id, format_exc())
                        continue

                    if dock_item is not None:
                        if dock_item.float_default:
                            ops.append(FloatItem(item=decl.id))
                        else:
                            ops.append(InsertTab(item=decl.id,
                                                 target=anchor))

                self.engine.observe('progress', monitor.process_news)
                if dock_item:
                    dock_item.monitor = monitor
                monitor.start()

            if ops:
                dock_area.update_layout(ops)

        # Executed in the main thread to avoid GUI update issues.
        schedule_and_block(start_monitors, (self, measurement), priority=100)

    def _stop_monitors(self, measurement):
        """Disconnect the monitors from the engine and stop them.

        The monitors windows is not hidden as the user may want to check it
        later.

        """
        def stop_monitors(engine, measurement):
            """Stop the monitors.

            Executed on the main thread.

            """
            if engine:
                engine.unobserve('news')
            for monitor in measurement.monitors.values():
                monitor.stop()

        # Executed in the main thread to avoid GUI update issues.
        schedule_and_block(stop_monitors, (self.engine, measurement),
                           priority=100)

    def _check_for_pause_or_stop(self):
        """Check if a pause or stop request is pending and process it.

        Returns
        -------
        should_stop : bool
            Booelan indicating whether or not the execution of the measurement
            should stop.

        """
        flag = self._state

        if flag.test('stop_attempt'):
            return False

        if flag.test('pause_attempt'):
            flag.clear('pause_attempt')
            self._set_measurement_state('PAUSED', 'The measurement is paused.')
            flag.set('paused')

            while True:
                if flag.wait(0.1, 'resuming'):
                    flag.clear('resuming')
                    self._set_measurement_state('RUNNING',
                                                'The measurement has resumed.')
                    return True

                if flag.test('stop_attempt'):
                    return False

        return True

    # Those must post update of measurement.status and remove observers
    def _watch_engine_state(self, change):
        """Observe engine state to notify that the engine paused or resumed.

        """
        if change['value'] == 'Paused':
            self._state.clear('pause_attempt')
            self.engine.unobserve('status', self._watch_engine_state)
            self._set_measurement_state('PAUSED', 'The measurement is paused.')
            self._state.set('paused')

        elif change['value'] == 'Running':
            self._state.clear('resuming')
            self.engine.unobserve('status', self._watch_engine_state)
            self._set_measurement_state('RUNNING',
                                        'The measurement has resumed.')

    def _watch_hook_state(self, change):
        """Observe hook paused/resumed events to validate pausing/resuming.

        """
        if change['name'] == 'paused':
            self._active_hook.unobserve('status', self._watch_hook_state)
            self._set_measurement_state('PAUSED', 'The measurement is paused.')
            self._state.clear('pause_attempt')
            self._state.set('paused')

        elif change['name'] == 'resumed':
            self._state.clear('resuming')
            self._active_hook.unobserve('status', self._watch_hook_state)
            self._set_measurement_state('RUNNING',
                                        'The measurement has resumed.')

    def _set_measurement_state(self, status, infos, measurement=None,
                               clear=False):
        """Set the measurement status and infos in the main thread.

        """
        def set_state(processor, status, infos, meas, clear):
            if meas:
                processor.running_measurement = meas
            measurement = processor.running_measurement
            measurement.status = status
            measurement.infos = infos
            if clear:
                processor.running_measurement = None

        # Executed in the main thread to avoid GUI update issues.
        schedule_and_block(set_state,
                           (self, status, infos, measurement, clear),
                           priority=100)

    def _stop_engine(self):
        """Stop the engine.

        """
        logger.debug('Stopping engine')
        engine = self.engine
        engine.shutdown()
        i = 0
        while engine and engine.status != 'Stopped':
            sleep(0.5)
            i += 1
            if i > 10:
                engine.shutdown(force=True)

    def _clear_state(self):
        """Clear the state when starting while preserving persistent settings.

        """
        flags = list(self._state.flags)
        flags.remove('processing')
        flags.remove('continuous_processing')
        self._state.clear(*flags)

    def _post_setattr_continuous_processing(self, old, new):
        """Make sure the internal bit flag does reflect the real setting.

        """
        if new:
            self._state.set('continuous_processing')
        else:
            self._state.clear('continuous_processing')


def errors_to_msg(errors):
    """Convert a dictionary of errors in a well formatted message.

    """
    err = '\n'.join(('- %s : %s' % (k, v) for k, v in errors.items()))
    return 'The following errors occured :\n' + err
