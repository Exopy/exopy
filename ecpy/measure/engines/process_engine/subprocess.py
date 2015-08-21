# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
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
import warnings
import sys
from multiprocessing import Process

from ....app.log.tools import (StreamToLogRedirector, DayRotatingTimeHandler)
from ....tasks.api import build_task_from_config
from ..tools import MeasureSpy


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
                 task_stop, process_stop):
        super(TaskProcess, self).__init__(name='MeasureProcess')
        self.daemon = True
        self.task_pause = task_pause
        self.task_paused = task_paused
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

        # TODO test if this is still necessary with latest version
        # Ugly patch to avoid pyvisa complaining about missing filters
        warnings.simplefilter("ignore")

        # Redirecting stdout and stderr to the logging system.
        logger = logging.getLogger()
        redir_stdout = StreamToLogRedirector(logger)
        sys.stdout = redir_stdout
        redir_stderr = StreamToLogRedirector(logger, 'stderr')
        sys.stderr = redir_stderr
        logger.info('Logger parametrised')

        logger.info('Process running')
        self.pipe.send('READY')
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
                name, config, build, runtime, entries, database =\
                    self.pipe.recv()

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

                log_path = os.path.join(root.get_from_database('default_path'),
                                        name + '.log')
                if os.path.isfile(log_path):
                    os.remove(log_path)
                self.meas_log_handler = DayRotatingTimeHandler(log_path,
                                                               mode='w',
                                                               maxBytes=10**6)
                aux = '%(asctime)s | %(levelname)s | %(message)s'
                formatter = logging.Formatter(aux)
                self.meas_log_handler.setFormatter(formatter)
                logger.addHandler(self.meas_log_handler)

                # Pass the events signaling the task it should stop or pause
                # to the task and make the database ready.
                root.should_pause = self.task_pause
                root.paused = self.task_paused
                root.should_stop = self.task_stop
                root.database.prepare_for_running()

                # Perform the checks.
                check, errors = root.check()

                # If checks pass perform the measure.
                if check:
                    logger.info('Check successful')
                    root.perform()
                    result = ['', '', '']
                    if self.task_stop.is_set():
                        result[0] = 'INTERRUPTED'
                        result[2] = 'Measure {} was stopped'.format(name)
                    else:
                        result[0] = 'COMPLETED'
                        result[2] = 'Measure {} succeeded'.format(name)

                    if self.process_stop.is_set():
                        result[1] = 'STOPPING'
                    else:
                        result[1] = 'READY'

                    self.pipe.send(tuple(result))

                # They fail, mark the measure as failed and go on.
                else:
                    mes = 'Tests failed, see log for full records.'
                    self.pipe.send(('FAILED', 'READY', mes))

                    # Log the tests that failed.
                    fails = errors.iteritems()
                    message = '\n'.join('{} : {}'.format(path, mes)
                                        for path, mes in fails)
                    logger.critical(message)

                # If a spy was started kill it
                if entries:
                    spy.close()
                    del spy

            except IOError:
                pass

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
                    'class': 'hqc_meas.utils.log.tools.QueueHandler',
                    'queue': self.log_queue,
                },
            },
            'root': {
                'level': 'INFO',
                'handlers': ['queue']
            },
        }
        logging.config.dictConfig(config_worker)
