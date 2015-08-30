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
from queue import Queue

import enaml
from atom.api import Atom, Typed, Int

from .engines import BaseEngine
from .measure import Measure

logger = logging.getLogger(__name__)


INVALID_MEASURE_STATUS = ['EDITING', 'SKIPPED', 'FAILED', 'COMPLETED',
                          'INTERRUPTED']


class MeasureProcessingFlags(IntEnum):
    """Enumeration defining the bit flags used by the measure plugin.

    """
    processing = 1
    running_pre_hooks = 16
    running_main = 32
    running_post_hooks = 64
    stop_attempt = 2
    stop_processing = 4
    no_post_exec = 8


class MeasureProcessor(Atom):
    """
    """
    #: Currently run measure or last measure run.
    running_measure = Typed(Measure)

    #: Instance of the currently used engine.
    engine_instance = Typed(BaseEngine)

    # Internal flags used to keep track of the execution state.
    execution_state = Int()

    def start_measure(self, measure):
        """Start a new measure.

        """
        # Discard old monitors if there is any remaining.
        if self.running_measure:
            for monitor in self.running_measure.monitors.values():
                monitor.stop()

        measure.enter_running_state()
        self.running_measure = measure

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

    def pause_measure(self):
        """Pause the currently active measure.

        """
        logger.info('Pausing measure {}.'.format(self.running_measure.name))
        self.engine_instance.pause()

    def resume_measure(self):
        """Resume the currently paused measure.

        """
        logger.info('Resuming measure {}.'.format(self.running_measure.name))
        self.engine_instance.resume()

    def stop_measure(self, no_post_exec=False, force=False):
        """Stop the currently active measure.

        """
        logger.info('Stopping measure {}.'.format(self.running_measure.name))
        self.flags |= MeasureProcessingFlags.stop_attempt
        if no_post_exec:
            self.flags |= MeasureProcessingFlags.no_post_exec
        self.engine_instance.stop()

    def stop_processing(self, no_post_exec=False, force=False):
        """Stop processing the enqueued measure.

        """
        logger.info('Stopping measure {}.'.format(self.running_measure.name))
        self.flags |= (MeasureProcessingFlags.stop_attempt |
                       MeasureProcessingFlags.stop_processing)
        if self.flags and MeasureProcessingFlags.processing:
            self.flags &= ~MeasureProcessingFlags.processing
        if no_post_exec:
            self.flags |= MeasureProcessingFlags.no_post_exec
        self.engine_instance.exit()

    # XXXX Rely on kwarg
    def force_stop_measure(self):
        """Force the engine to stop performing the current measure.

        """
        logger.info('Exiting measure {}.'.format(self.running_measure.name))
        self.flags |= MeasureProcessingFlags.no_post_exec
        self.engine_instance.force_stop()

    # XXXX Rely on kwarg
    def force_stop_processing(self):
        """Force the engine to exit and stop processing measures.

        """
        logger.info('Exiting measure {}.'.format(self.running_measure.name))
        self.flags |= (MeasureProcessingFlags.stop_processing |
                       MeasureProcessingFlags.no_post_exec)
        if self.flags & MeasureProcessingFlags.processing:
            self.flags &= ~MeasureProcessingFlags.processing
        self.engine_instance.force_exit()

    def find_next_measure(self):
        """Find the next runnable measure in the queue.

        Returns
        -------
        measure : Measure
            First valid measurement in the queue or None if there is no
            available measure.

        """
        enqueued_measures = self.enqueued_measures
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

    # --- Private API ---------------------------------------------------------

    def _listen_to_engine(self, status, infos):
        """Observer for the engine notifications.

        """
        meas = self.running_measure

        if not self.flags and MeasureProcessingFlags.no_post_exec:
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
                if engine and self.engine_policy == 'stop':
                        self._stop_engine()
                self.flags = 0

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

    def _skip_measure(self, reason, message):
        """Skip a measure and provide an explanation for it.

        """
        # Simulate a message coming from the engine.
        done = {'value': (reason, message)}

        # Break a potential high statck as this function would not exit
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
