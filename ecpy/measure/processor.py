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

from .engines import BaseEngine, TaskInfos
from .measure import Measure
from ..utils.bi_flag import BitFlag

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
    #: Reference to the measure plugin.
    plugin = ForwardTyped(plugin)

    #: Currently run measure or last measure run.
    running_measure = Typed(Measure)

    #: Instance of the currently used engine.
    engine = Typed(BaseEngine)

    #: Boolean indicating whether or not process all enqueued measures.
    continuous_processing = Bool(True)

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
        else:
            with self._lock:
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
        else:
            with self._lock:
                if self._active_hook:
                    self._active_hook.resume()
                    self._active_hook.observe('resumed',
                                              self._watch_hook_state)

    def stop_measure(self, no_post_exec=False, force=False):
        """Stop the currently active measure.

        """
        logger.info('Stopping measure {}.'.format(self.running_measure.name))
        self._state.set('stop_attempt')
        if no_post_exec or force:
            self._state.set('no_post_exec')

        if self._state.test('running_main'):
            self._engine.stop(force)
        else:
            with self._lock:
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
            with self._lock:
                if self._active_hook:
                    self._active_hook.stop(force)

    # --- Private API ---------------------------------------------------------

    #: Background thread handling the measure execution
    _thread = Value()

    #: Internal flags used to keep track of the execution state.
    _state = Typed(BitFlag,
                   ('processing', 'running_pre_hooks', 'running_main',
                    'running_post_hooks', 'pause_attempt', 'paused',
                    'stop_attempt', 'stop_processing', 'no_post_exec',
                    'continuous_processing')
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

            # Discard old monitors if there is any remaining.
            if self.running_measure:
                for monitor in self.running_measure.monitors.values():
                    enaml.application.deferred_call(monitor.stop)

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
                enaml.application.deferred_call(setattr, meas, 'status',
                                                'RUNNING')
                enaml.application.deferred_call(setattr, meas, 'infos',
                                                'The measure is being run.')

                msg = 'Starting execution of measure %s'
                logger.info(msg % meas.name + meas.id)

                stage, status, errors = self._run_measure(meas)

            # If no measure remains stop.
            else:
                break

            # Process the result of the measure.

            # First create an error message if pertinent.
            if errors:
                err_msg = errors_to_msg(errors)

            # Log the result.
            mess = 'Measure %s processed, status : %s' % (meas.name, status)
            if errors:
                mess += '\n' + err_msg
            logger.info(mess)

            # Update the status and infos.
            enaml.application.deferred_call(setattr, meas, 'status', status)

            if status == 'COMPLETED':
                msg = 'The measure was successfully performed'
            elif status == 'INTERRUPTED':
                msg = 'The measure execution was interrupted by the user.'
            else:
                msg = 'While executing the %s : ' % stage + err_msg
            enaml.application.deferred_call(setattr, meas, 'infos', msg)

            # If we are supposed to stop, stop.
            if not self._state.test('continuous_processing'):
                break

        if self.engine and self.plugin.engine_policy == 'stop':
            self._stop_engine()

        self._state.clear('processing')

    def _run_measure(self, measure):
        """Run a single measure.

        """
        # Switch to running state.
        measure.enter_running_state()

        core = self.workbench.get_plugin('enaml.workbench.core')
        meas_id = measure.name + '_' + measure.id

        # Checking build dependencies, if present simply request runtimes.
        if 'build_deps' in measure.store and 'runtime_deps' in measure.store:

            # Requesting runtime, so that we get permissions.
            runtimes = measure.store['runtime_deps']
            cmd = 'ecpy.app.dependencies.request_runtimes'
            deps = core.invoke_command(cmd,
                                       {'obj': measure.root_task,
                                        'owner': self.manifest.id,
                                        'dependencies': runtimes},
                                       )
            # XXXX
            res, cause, infos = self.check_for_dependencies_errors(measure,
                                                                   deps)
            if not res:
                if cause == 'errors':
                    return 'FAILED', ''
                else:
                    return 'SKIPPED', ''

        else:
            # Collect build and runtime dependencies.
            cmd = 'ecpy.app.dependencies.collect'
            b_deps, r_deps = core.invoke_command(cmd,
                                                 {'obj': measure.root_task,
                                                  'dependencies': ['build',
                                                                   'runtime'],
                                                  'owner': self.manifest.id})

            # XXXX
            res = self.check_for_dependencies_errors(measure, b_deps)
            res &= self.check_for_dependencies_errors(measure, r_deps)
            if not res:
                return

        # Records that we got access to all the runtimes.
        mess = ('The use of all runtime resources have been granted to the '
                'measure %s' % meas_id)
        logger.info(mess.replace('\n', ' '))

        # Run checks now that we have all the runtimes.
        res, errors = measure.run_checks(self.workbench)
        if not res:
            # XXXX
            cmd = 'ecpy.app.errors.signal'
            msg = 'Measure %s failed to pass the checks.' % measure.name
            core.invoke_command(cmd, {'kind': 'measure-error',
                                      'message': msg % (measure.name),
                                      'errors': errors})

            return 'FAILED', 'Failed to pass the checks'

        # Now that we know the measure is going to run save it.
        default_filename = meas_id + '.meas.ini'
        path = os.path.join(measure.root_task.default_path, default_filename)
        measure.save(path)

        logger.info('Starting measure {}.'.format(meas_id))

        # Execute all pre-execution hooks.
        result, errors = self._run_pre_execution()
        if not result:
            return 'pre-hooks', 'FAILED', errors

        self._check_for_pause()

        # Connect new monitors, and start them.
        ui_plugin = self.workbench.get_plugin('enaml.workbench.ui')
        for monitor in measure.monitors.values():
            self.engine.observe('news', monitor.process_news)
            monitor.start(ui_plugin.window)

        # Ask the engine to start the measure.
        # XXXX
        result, msg = self.engine.perform(TaskInfos())
        if not result:
            return 'main task', 'FAILED', {'engine': msg}

        # Disconnect monitors.
        engine = self._engine
        if engine:
            engine.unobserve('news')

        self._check_for_pause()

        # Execute all post-execution hooks if pertinent.
        if not self._state.test('no_post_exec'):
            result, errors = self._run_pre_execution()
            if not result:
                return 'post-hooks', 'FAILED', errors

        # Release runtime dependencies.
        core = self.workbench.get_plugin('enaml.workbench.core')
        cmd = 'ecpy.app.dependencies.release_runtimes'
        core.invoke_command(cmd,
                            {'dependencies': measure.store['runtime_deps'],
                             'owner': self.plugin.manifest.id})

        return 'end', 'COMPLETED', {}

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
            self._check_for_pause()
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
            self._check_for_pause()
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

    # Those must post update of measure.status and remove observers
    def _check_for_pause(self):
        """Check whether or a pause was requested and handle it.

        """
        pass# XXXX

    def _watch_engine_state(self, change):
        """Observe engine state to notify that the engine paused or resumed.

        """
        pass# XXXX

    def _watch_hook_state(self, change):
        """Observe hook paused/resumed events to validate pausing/resuming.

        """
        pass# XXXX

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
