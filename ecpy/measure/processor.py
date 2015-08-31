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
from enum import IntEnum
from traceback import format_exc
from threading import Thread

import enaml
from atom.api import Atom, Typed, ForwardTyped, Value, Bool

from .engines import BaseEngine
from .measure import Measure

logger = logging.getLogger(__name__)


INVALID_MEASURE_STATUS = ['EDITING', 'SKIPPED', 'FAILED', 'COMPLETED',
                          'INTERRUPTED']


# XXXX Turn into a bitflag
class MeasureProcessingFlags(IntEnum):
    """Enumeration defining the bit flags used by the measure plugin.

    """
    processing = 1
    running_pre_hooks = 2
    running_main = 4
    running_post_hooks = 8
    pause_attempt = 16
    paused = 32
    stop_attempt = 64
    stop_processing = 128
    no_post_exec = 256

# XXXX
def plugin():
    """
    """
    from .plugin import MeasurePlugin
    return MeasurePlugin


# XXXX
class MeasureProcessor(Atom):
    """
    """
    #: Reference to the measure plugin.
    plugin = ForwardTyped(plugin)

    #: Currently run measure or last measure run.
    running_measure = Typed(Measure)

    #: Instance of the currently used engine.
    engine_instance = Typed(BaseEngine)

    #: Boolean indicating whether or not process all enqueued measures.
    continuous_processing = Bool(True)

    def start_processing(self, measure):
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

        self._thread = Thread(target=self._run_measures,
                              args=(measure,))
        self._thread.start()

    def perform_task(self, task_infos):
        """Execute a task.

        Returns
        -------
        # XXXX

        """
        return self._engine_instance.perform(task_infos)

    def pause_measure(self):
        """Pause the currently active measure.

        """
        logger.info('Pausing measure {}.'.format(self.running_measure.name))
        self._state.set('pause_attempt')
        self.engine_instance.pause()

    def resume_measure(self):
        """Resume the currently paused measure.

        """
        logger.info('Resuming measure {}.'.format(self.running_measure.name))
        self._state.clear('pause_attempt')
        self.engine_instance.resume()

    def stop_measure(self, no_post_exec=False, force=False):
        """Stop the currently active measure.

        """
        logger.info('Stopping measure {}.'.format(self.running_measure.name))
        self._state.set('stop_attempt')
        if no_post_exec or force:
            self._state.set('no_post_exec')
        self.engine_instance.stop(force=force)

    def stop_processing(self, no_post_exec=False, force=False):
        """Stop processing the enqueued measure.

        """
        logger.info('Stopping measure {}.'.format(self.running_measure.name))
        self._state.set('stop_attempt', 'stop_processing')
        self._state.clear('processing')
        if no_post_exec or force:
            self._state.set('no_post_exec')
        self.engine_instance.exit(force=force)

    # --- Private API ---------------------------------------------------------

    #: Background thread handling the measure execution
    _thread = Value()

    #: Internal flags used to keep track of the execution state.
    _state = Typed(BitFlag)


    def _run_measures(self, measure):
        """
        """
        # If the engine does not exist, create one.
        plugin = self.plugin
        if not self.engine_instance:
            self.engine_instance = plugin.create('engine',
                                                 plugin.selected_engine)

        # Process enqueued measure as long as we are supposed to.
        while not self.execution_state & MeasureProcessingFlags.stop_processing:

            # Discard old monitors if there is any remaining.
            if self.running_measure:
                for monitor in self.running_measure.monitors.values():
                    enaml.application.deferred_call(monitor.stop)

            self._cleanup()
            meas = self.running_measure

            if not self.flags & MeasureProcessingFlags.no_post_exec:
                # Post execution should provide a way to interrupt their execution.
                meas.run_post_execution(self.workbench)

            mess = 'Measure {} processed, status : {}'.format(meas.name, status)
            logger.info(mess)

            # Releasing runtime dependencies.
            core = self.workbench.get_plugin('enaml.workbench.core')

            cmd = 'ecpy.app.dependencies.release_runtimes'
            core.invoke_command(cmd, {'dependencies': meas.store['runtime_deps'],
                                      'owner': self.manifest.id})

            # Disconnect monitors.
            engine = self.engine_instance
            if engine:
                engine.unobserve('news')

            # If we are supposed to stop, stop.
            if engine and self.flags & MeasureProcessingFlags.stop_processing:
                if self.engine_policy == 'stop':
                    self._stop_engine()
                self.flags = 0

            # Otherwise find the next measure, if there is none stop the engine.
            else:
                meas = self.find_next_measure()
                if meas is not None:
                    self.flags = 0
                    self.start_measure(meas)
                else:
                    if engine and self.plugin.engine_policy == 'stop':
                        self._stop_engine()
                    self.flags = 0

        if engine and self.plugin.engine_policy == 'stop':
            self._stop_engine()
        self.flags = 0

    def _run_measure(self, measure):
        """
        """
        measure.enter_running_state()
        enaml.application.deferred_call(setattr, self, 'running_measure',
                                        measure)

        self.flags |= MeasureProcessingFlags.processing

        core = self.workbench.get_plugin('enaml.workbench.core')

        # Checking build dependencies, if present simply request runtimes.
        if 'build_deps' in measure.store and 'runtime_deps' in measure.store:
            # Requesting runtime, so that we get permissions.

            runtimes = measure.store['runtime_deps']
            cmd = 'ecpy.app.dependencies.request_runtimes'
            deps = core.invoke_command(cmd,
                                       {'obj': measure.root_task,
                                        'owner': [self.manifest.id],
                                        'dependencies': runtimes},
                                       )
            res = self.check_for_dependencies_errors(measure, deps, skip=True)
            if not res:
                return

        else:
            # Collect build and runtime dependencies.
            cmd = 'ecpy.app.dependencies.collect'
            b_deps, r_deps = core.invoke_command(cmd,
                                                 {'obj': measure.root_task,
                                                  'dependencies': ['build',
                                                                   'runtime'],
                                                  'owner': self.manifest.id})

            res = self.check_for_dependencies_errors(measure, b_deps,
                                                     skip=True)
            res &= self.check_for_dependencies_errors(measure, r_deps,
                                                      skip=True)
            if not res:
                return

        # Records that we got access to all the runtimes.
        mess = ('The use of all runtime resources have been granted to the '
                'measure %s' % measure.name)
        logger.info(mess.replace('\n', ' '))

        # Run checks now that we have all the runtimes.
        res, errors = measure.run_checks(self.workbench)
        if not res:
            cmd = 'ecpy.app.errors.signal'
            msg = 'Measure %s failed to pass the checks.' % measure.name
            core.invoke_command(cmd, {'kind': 'measure-error',
                                      'message': msg % (measure.name),
                                      'errors': errors})

            self._skip_measure('FAILED', 'Failed to pass the checks')
            return

        # Now that we know the measure is going to run save it.
        default_filename = measure.name + '_' + measure.id + '.meas.ini'
        path = os.path.join(measure.root_task.default_path, default_filename)
        measure.save(path)

        # Start the engine if it has not already been done.
        if not self.engine_instance:
            decl = self.engines[self.selected_engine]
            engine = decl.factory(decl, self.workbench)
            self.engine_instance = engine

            # Connect signal handler to engine.
            engine.observe('completed', self._listen_to_engine)

        engine = self.engine_instance

        # Call engine prepare to run method.
        engine.prepare_to_run(measure)

        # Execute all pre-execution hook.
        measure.run_pre_execution()

        # Get a ref to the main window.
        ui_plugin = self.workbench.get_plugin('enaml.workbench.ui')
        # Connect new monitors, and start them.
        for monitor in measure.monitors.values():
            engine.observe('news', monitor.process_news)
            monitor.start(ui_plugin.window)

        logger.info('''Starting measure {}.'''.format(measure.name))
        # Ask the engine to start the measure.
        engine.run()

    def _run_pre_execution(self, workbench, **kwargs):
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
                res, report = hook.run(workbench, self, **kwargs)
                result &= res
                full_report[id] = report
            except Exception:
                result = False
                full_report[id] = format_exc()

        return result, full_report

    def _run_post_execution(self, workbench, **kwargs):
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
                res, report = hook.run(workbench, self, **kwargs)
            except Exception:
                result = False
                full_report[id] = format_exc()

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

    def _skip_measure(self, reason, message):
        """Skip a measure and provide an explanation for it.

        """
        # Simulate a message coming from the engine.
        done = {'value': (reason, message)}

        # Break a potential high stack as this function would not exit
        # if a new measure is started.
        enaml.application.deferred_call(self._listen_to_engine, done)

    def _stop_engine(self):
        """Stop the engine.

        """
        engine = self.engine_instance
        self.stop_processing()
        i = 0
        while engine and engine.active:
            sleep(0.5)
            i += 1
            if i > 10:
                self.force_stop_processing()

    def _clean_execution_flag(self):
        """Clean the execution flag when starting while preserving persistent
        settings.

        """
        old = self.state.test('continuous')
        self._state.clear()
        if old:
            self._state.set('continuous')

    def _post_setattr_continuous_processing(self, old, new):
        """Make sure the internal bit flag does reflect the real setting.

        """
        if new:
            self._state.clear('continuous')
        else:
            self._state.set('continuous')
