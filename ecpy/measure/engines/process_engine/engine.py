# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Engine executing the measure in a different process.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import logging
from multiprocessing import Pipe
from multiprocessing.queues import Queue
from multiprocessing.synchronize import Event
from threading import Thread
from threading import Event as tEvent

from atom.api import Typed, Value, Tuple, Bool
from enaml.workbench.api import Workbench
from enaml.application import deferred_call


from ....utils.log.tools import QueueLoggerThread
from ..base_engine import BaseEngine
from ..tools import ThreadMeasureMonitor
from .subprocess import TaskProcess


class ProcessEngine(BaseEngine):
    """An engine executing the measurement it is sent in a different process.

    """
    #: Reference to the application workbench
    workbench = Typed(Workbench)

    # XXXX
    def prepare_to_run(self, measure):
        """Set everything so that teh measure is ready to start.

        """

        runtime_deps = root.run_time

        # Get ConfigObj describing measure.
        root.update_preferences_from_members()
        config = root.task_preferences

        # Store infos sent about the next measure to process.
        self._infos = (name, config, build_deps, runtime_deps,
                       monitored_entries)

        # Clear all the flags.
        self._meas_pause.clear()
        self._meas_paused.clear()
        self._meas_stop.clear()
        self._stop.clear()
        self._force_stop.clear()
        self._stop_requested = False

        # If the process does not exist or is dead create a new one.
        if not self._process or not self._process.is_alive():
            self._pipe, process_pipe = Pipe()
            self._process = TaskProcess(process_pipe,
                                        self._log_queue,
                                        self._monitor_queue,
                                        self._meas_pause,
                                        self._meas_paused,
                                        self._meas_stop,
                                        self._stop)
            self._process.daemon = True

            self._log_thread = QueueLoggerThread(self._log_queue)
            self._log_thread.daemon = True
            self._log_thread.start()

            self._monitor_thread = ThreadMeasureMonitor(self,
                                                        self._monitor_queue)
            self._monitor_thread.daemon = True
            self._monitor_thread.start()

            self._pause_thread = None

            # Start process.
            self._process.start()
            self.active = True

            # Start main communication thread.
            self._com_thread = Thread(group=None,
                                      target=self._process_listener)
            self._com_thread.start()

        self.measure_status = ('PREPARED', 'Engine ready to process.')

    def perform(self, task):
        """Execute a given task hierarchy.

        This is needed for pre and post execution hook needing to execute
        arbitrary tasks.

        """
        raise NotImplementedError()

    def run(self):
        """
        """
        self._starting_allowed.set()

        self.measure_status = ('RUNNING', 'Measure running.')

    def pause(self):
        self.measure_status = ('PAUSING', 'Waiting for measure to pause.')
        self._meas_pause.set()

        self._pause_thread = Thread(target=self._wait_for_pause)
        self._pause_thread.start()

    def resume(self):
        self._meas_pause.clear()
        self.measure_status = ('RUNNING', 'Measure have been resumed.')

    def stop(self):
        self._stop_requested = True
        self._meas_stop.set()

    def exit(self):
        self._stop_requested = True
        self._meas_stop.set()
        self._stop.set()
        # Everything else handled by the _com_thread and the process.

    def force_stop(self):
        self._stop_requested = True
        # Just in case the user calls this directly. Will signal all threads to
        # stop (save _com_thread).
        self._stop.set()
        self._log_queue.put(None)
        self._monitor_queue.put((None, None))

        # Set _force_stop to stop _com_thread.
        self._force_stop.set()

        # Terminate the process and make sure all threads stopped properly.
        self._process.terminate()
        self._log_thread.join()
        self._monitor_thread.join()
        self._com_thread.join()
        self.active = False
        if self._processing.is_set():
            self.done = ('INTERRUPTED', 'The user forced the system to stop')
            self._processing.clear()

        # Discard the queues as they may have been corrupted when the process
        # was terminated.
        self._log_queue = Queue()
        self._monitor_queue = Queue()

    def force_exit(self):
        self.force_stop()

    # --- Private API ---------------------------------------------------------

    #: Flag indicating that the user requested the measure to stop.
    _stop_requested = Bool()

    #: Interprocess event used to pause the subprocess current measure.
    _meas_pause = Typed(Event, ())

    #: Interprocess event signaling the subprocess current measure is paused.
    _meas_paused = Typed(Event, ())

    #: Interprocess event used to stop the subprocess current measure.
    _meas_stop = Typed(Event, ())

    #: Interprocess event used to stop the subprocess.
    _stop = Typed(Event, ())

    #: Flag signaling that a forced exit has been requested
    _force_stop = Value(tEvent())

    #: Flag indicating the process is waiting for a measure.
    _processing = Value(tEvent())

    #: Flag indicating the communication thread it can send the next measure.
    _starting_allowed = Value(tEvent())

    #: Temporary tuple to store the data to be sent to the process when a
    #: new measure is ready.
    _temp = Tuple()

    #: Current subprocess.
    _process = Typed(TaskProcess)

    #: Connection used to send and receive messages about execution (type
    #: ambiguous when the OS is not known)
    _pipe = Value()

    #: Thread in charge of transferring measure to the process.
    _com_thread = Typed(Thread)

    #: Inter-process queue used by the subprocess to transmit its log records.
    _log_queue = Typed(Queue, ())

    #: Thread in charge of collecting the log message coming from the
    #: subprocess.
    _log_thread = Typed(Thread)

    #: Inter-process queue used by the subprocess to send the values of the
    #: observed database entries.
    _monitor_queue = Typed(Queue, ())

    #: Thread in charge of collecting the values of the observed database
    #: entries.
    _monitor_thread = Typed(Thread)

    #: Thread in charge of notifying the engine that the measure did pause
    #: after being asked to do so.
    _pause_thread = Typed(Thread)

    def _process_listener(self):
        """ Handle the communications with the worker process.

        Executed by the _com_thread.

        """
        logger = logging.getLogger(__name__)
        logger.debug('Starting listener')

        while not self._pipe.poll(2):
            if not self._process.is_alive():
                logger.critical('Subprocess was found dead unexpectedly')
                self._stop.set()
                self._log_queue.put(None)
                self._monitor_queue.put((None, None))
                self._cleanup(process=False)
                self.done = ('FAILED', 'Subprocess failed to start')
                return

        mess = self._pipe.recv()
        if mess != 'READY':
            logger.critical('Subprocess was found dead unexpectedly')
            self.done = ('FAILED', 'Subprocess failed to start')
            self._cleanup()
            return

        # Infinite loop waiting for measure.
        while not self._stop.is_set():

            # Wait for measure and check for stopping.
            while not self._starting_allowed.wait(1):
                if self._stop.is_set():
                    self._cleanup()
                    return

            self._processing.set()

            # Send the measure.
            self._pipe.send(self._temp)
            logger.debug('Measure {} sent'.format(self._temp[0]))

            # Empty _temp and reset flag.
            self._temp = tuple()
            self._starting_allowed.clear()

            # Wait for the process to finish the measure and check it has not
            # been killed.
            while not self._pipe.poll(1):
                if self._force_stop.is_set():
                    self._cleanup()
                    return

            # Here get message from process and react
            meas_status, int_status, mess = self._pipe.recv()
            logger.debug('Subprocess done performing measure')

            if int_status == 'STOPPING':
                self._cleanup()

            if meas_status == 'INTERRUPTED' and not self._stop_requested:
                meas_status = 'FAILED'
                mess = mess.replace('was stopped', 'failed')

            # This event should be handled in the main thread so that this one
            # can stay responsive otherwise the engine will be unable to
            # shutdown.
            deferred_call(setattr, self, 'done', (meas_status, mess))

            self._processing.clear()

        self._cleanup()

    def _cleanup(self, process=True):
        """ Helper method taking care of making sure that everybody stops.

        Parameters
        ----------
        process : bool
            Wether to join the worker process. Used when the process has been
            termintaed abruptly.

        """
        logger = logging.getLogger(__name__)
        logger.debug('Cleaning up')
        self._pipe.close()
        if process:
            self._process.join()
            logger.debug('Subprocess joined')
        self._log_thread.join()
        logger.debug('Log thread joined')
        self._monitor_thread.join()
        logger.debug('Monitor thread joined')
        if self._pause_thread:
            self._pause_thread.join()
            logger.debug('Pause thread joined')
        self.active = False

    def _wait_for_pause(self):
        """ Wait for the task paused event to be set.

        """
        stop_sig = self._stop
        paused_sig = self._meas_paused

        while not stop_sig.is_set():
            if paused_sig.wait(0.1):
                status = ('PAUSED', 'Measure execution is paused')
                deferred_call(setattr, self, 'measure_status', status)
                break
