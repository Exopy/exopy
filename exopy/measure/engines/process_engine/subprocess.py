# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Subprocess executing the tasks sent by the subprocess engine.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os
import logging
import logging.config
import sys
from multiprocessing import Process
from time import sleep

from ....utils.traceback import format_exc
from ....app.log.tools import (StreamToLogRedirector, DayRotatingTimeHandler)
from ....tasks.api import build_task_from_config
from ..utils import MeasureSpy
from ...processor import errors_to_msg


class TaskProcess(Process):
    """Process taking care of performing the measures.

    When started this process sets up a logger redirecting all records to a
    queue. It then redirects stdout and stderr to the logging system. Then as
    long as it is not stopped it waits for the main process to send a
    measures through the pipe. Upon reception of the `ConfigObj` object
    describing the measure it rebuilds it, set up a logger for that specific
    measure and if necessary starts a spy transmitting the value of all
    monitored entries to the main process. It finally run the checks of the
    measure and run it. It can be interrupted by setting an event and upon
    exit close the communication pipe and signal all listeners that it is
    closing.

    Parameters
    ----------
    pipe :
        Pipe used to communicate with the parent process which is transferring
        the measure to perform.

    log_queue :
        Queue in which all log records are sent to be procesed later in the
        main process.

    monitor_queue :
        Queue in which all the informations the user asked to monitor during
        the measurement are sent to be processed in the main process.

    task_pause :
        Event set when the user asked the running measurement to pause.

    task_paused :
        Event set when the current measure is paused.

    task_stop :
        Event set when the user asked the running measurement to stop.

    process_stop :
        Event set when the user asked the process to stop.

    Attributes
    ----------
    meas_log_handler : log handler
        Log handler used to save the running measurement specific records.

    see `Parameters`

    Methods
    -------
    run():
        Method called when the new process starts.

    """

    def __init__(self, pipe, log_queue, monitor_queue, task_pause, task_paused,
                 task_resumed, task_stop, process_stop):
        super(TaskProcess, self).__init__(name='exopy.MeasureProcess')
        self.daemon = True
        self.task_pause = task_pause
        self.task_paused = task_paused
        self.task_resumed = task_resumed
        self.task_stop = task_stop
        self.process_stop = process_stop
        self.pipe = pipe
        self.log_queue = log_queue
        self.monitor_queue = monitor_queue
        self.meas_log_handler = None

    def run(self):
        """Method called when the new process starts.

        For a complete description of the workflow see the class
        docstring.

        """
        self._config_log()

        # Redirecting stdout and stderr to the logging system.
        logger = logging.getLogger()
        redir_stdout = StreamToLogRedirector(logger)
        sys.stdout = redir_stdout
        redir_stderr = StreamToLogRedirector(logger, 'stderr')
        sys.stderr = redir_stderr
        logger.info('Logger parametrised')

        logger.info('Process running')

        while not self.process_stop.is_set():

            # Prevent us from crash if the pipe is closed at the wrong moment.
            try:

                # Wait for a measurement.
                while not self.pipe.poll(2):
                    if self.process_stop.is_set():
                        break

                if self.process_stop.is_set():
                    break

                # Get the measure.
                try:
                    name, config, build, runtime, entries, database, checks =\
                        self.pipe.recv()
                except Exception:
                    logger.error('Failed to receive measure infos :\n' +
                                 format_exc())
                    sleep(1)
                    return
                self.pipe.send(True)

                # Build it by using the given build dependencies.
                root = build_task_from_config(config, build, True)

                # Set the specific root database values.
                for k, v in database.items():
                    root.write_in_database(k, v)

                # Give all runtime dependencies to the root task.
                root.run_time = runtime

                logger.info('Task built')

                # There are entries in the database we are supposed to
                # monitor start a spy to do it.
                if entries:
                    spy = MeasureSpy(self.monitor_queue, entries,
                                     root.database)

                # Set up the logger for this specific measurement.
                if self.meas_log_handler is not None:
                    logger.removeHandler(self.meas_log_handler)
                    self.meas_log_handler.close()
                    self.meas_log_handler = None

                log_path = os.path.join(root.default_path, name + '.log')
                self.meas_log_handler = DayRotatingTimeHandler(log_path)

                aux = '%(asctime)s | %(levelname)s | %(message)s'
                formatter = logging.Formatter(aux)
                self.meas_log_handler.setFormatter(formatter)
                logger.addHandler(self.meas_log_handler)

                # Pass the events signaling the task it should stop or pause
                # to the task and make the database ready.
                root.should_pause = self.task_pause
                root.paused = self.task_paused
                root.should_stop = self.task_stop
                root.resumed = self.task_resumed

                # Perform the checks.
                if checks:
                    check, errors = root.check()
                else:
                    logger.info('Tests skipped')
                    check = True

                # If checks pass perform the measure.
                if check:
                    logger.info('Check successful')
                    result = root.perform()

                    self.pipe.send((result, root.errors))

                # They fail, mark the measure as failed and go on.
                else:
                    self.pipe.send((False, errors))

                    # Log the tests that failed.
                    msg = 'Some test failed:\n' + errors_to_msg(errors)
                    logger.debug(msg)

                # If a spy was started kill it
                if entries:
                    spy.close()
                    del spy

            except Exception:
                logger.exception('Error occured during processing')
                break

        # Clean up before closing.
        logger.info('Process shuting down')
        if self.meas_log_handler:
            self.meas_log_handler.close()
        self.log_queue.put_nowait(None)
        self.monitor_queue.put_nowait((None, None))
        self.pipe.close()

    def _config_log(self):
        """Configuring the logger for the process.

        Sending all record to a multiprocessing queue.

        """
        config_worker = {
            'version': 1,
            'disable_existing_loggers': True,
            'handlers': {
                'queue': {
                    'class': 'exopy.app.log.tools.QueueHandler',
                    'queue': self.log_queue,
                },
            },
            'root': {
                'level': 'INFO',
                'handlers': ['queue']
            },
        }
        logging.config.dictConfig(config_worker)
