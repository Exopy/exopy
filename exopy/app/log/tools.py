# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""This module defines some tools to make easier the use of the logging module.

It provide tools to seamlessly convert stream information into log record so
that any `print` can get recorded, and others to process log emitted in a
subprocess.

:Contains:
    StreamToLogRedirector
        Simple class to redirect a stream to a logger.
    QueueHandler
        Logger handler putting records into a queue.
    GuiConsoleHandler
        Logger handler adding the message of a record to a GUI panel.
    QueueLoggerThread
        Thread getting log record from a queue and asking logging to handle
        them.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)


import logging
import os
import time
import datetime
from future.moves import queue
from future.builtins import str
from logging.handlers import TimedRotatingFileHandler
from threading import Thread
from enaml.application import deferred_call
from atom.api import Atom, Unicode, Int
import codecs


class StreamToLogRedirector(object):
    """Simple class to redirect a stream to a logger.

    Stream like object which can be used to replace `sys.stdout`, or
    `sys.stderr`.

    Parameters
    ----------
    logger : instance(`Logger`)
        Instance of a loger object returned by a call to logging.getLogger
    stream_type : {'stdout', 'stderr'}, optionnal
        Type of stream being redirected. Stderr stream are logged as CRITICAL

    Attributes
    ----------
    logger : instance(`Logger`)
        Instance of a loger used to log the received message

    """
    def __init__(self, logger, stream_type='stdout'):
        self.logger = logger
        if stream_type == 'stderr':
            self.write = self.write_error
        else:
            self.write = self.write_info

    def write_info(self, message):
        """Log the received message as info, used for stdout.

        The received message is first strip of starting and trailing
        whitespaces and line return.

        """
        message = message.strip()
        message = str(message)
        if message != '':
            self.logger.info(message)

    def write_error(self, message):
        """Log the received message as critical, used for stderr.

        The received message is first strip of starting and trailing
        whitespaces and line return.

        """
        message = message.strip()
        message = str(message)
        if message != '':
            self.logger.critical(message)

    def flush(self):
        """Useless function implemented for compatibility.

        """
        return None


# Copied and pasted from the logging module of Python 3.3
class QueueHandler(logging.Handler):
    """Handler sending events to a queue.

    Typically, it would be used together with a multiprocessing Queue to
    centralise logging to file in one process (in a multi-process application),
    so as to avoid file write contention between processes.
    Errors are silently ignored to avoid possible recursions and that's why
    this handler should be coupled to another, safer one.

    Parameters
    ----------
    queue :
        Queue to use to log the messages.

    """
    def __init__(self, queue):
        logging.Handler.__init__(self)
        self.queue = queue

    def enqueue(self, record):
        """Enqueue a record.

        The base implementation uses put_nowait. You may want to override
        this method if you want to use blocking, timeouts or custom queue
        implementations.

        """
        self.queue.put_nowait(record)

    def prepare(self, record):
        """ Prepares a record for queueing.

        The object returned by this method is enqueued. The base implementation
        formats the record to merge the message and arguments, and removes
        unpickleable items from the record in-place.

        You might want to override this method if you want to convert
        the record to a dict or JSON string, or send a modified copy
        of the record while leaving the original intact.

        """
        # The format operation gets traceback text into record.exc_text
        # (if there's exception data), and also puts the message into
        # record.message. We can then use this to replace the original
        # msg + args, as these might be unpickleable. We also zap the
        # exc_info attribute, as it's no longer needed and, if not None,
        # will typically not be pickleable.
        self.format(record)
        record.msg = record.message
        record.args = None
        record.exc_info = None
        return record

    def emit(self, record):
        """Emit a record.

        Writes the LogRecord to the queue, preparing it first.

        """
        try:
            self.enqueue(self.prepare(record))
        except Exception:
            # Don't try to handle the error as we might be redirecting sys.std
            # let another logger handle the issue.
            pass


class QueueLoggerThread(Thread):
    """Thread emptying a queue containing log record and sending them to the
    appropriate logger.

    Attributes
    ----------
    queue :
        Queue from which to collect log records.

    """
    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue
        self.flag = True

    def run(self):
        """ Pull any output from the queue while the listened process does not
        put `None` into the queue or somebody turn off the flag.

        """
        while self.flag:
            # Collect all display output from process
            try:
                record = self.queue.get(timeout=0.5)
                if record is None:
                    break
                logger = logging.getLogger(record.name)
                logger.handle(record)
            except queue.Empty:
                continue


class LogModel(Atom):
    """Simple object which can be used in a GuiHandler.

    """
    #: Text representing all the messages sent by the handler.
    #: Should not be altered by user code.
    text = Unicode()

    #: Maximum number of lines.
    buff_size = Int(1000)

    def clean_text(self):
        """Empty the text member.

        """
        self.text = ''
        self._lines = 0

    def add_message(self, message):
        """Add a message to the text member.

        """
        if self._lines > self.buff_size:
            self.text = self.text.split('\n', self._lines - self.buff_size)[-1]
        message = message.strip()
        message = str(message)
        message += '\n'

        self._lines += message.count('\n')
        self.text += message

    #: Number of lines.
    _lines = Int()


ERR_MESS = 'An error occured please check the log file for more details.'


class GuiHandler(logging.Handler):
    """Logger record sending the log message to an object which can be linked
    to a GUI.

    Errors are silently ignored to avoid possible recursions and that's why
    this handler should be coupled to another, safer one.

    Parameters
    ----------
    model : Atom
        Model object with a text member.

    Methods
    -------
    emit(record)
        Handle a log record by appending the log message to the model

    """
    def __init__(self, model):
        logging.Handler.__init__(self)
        self.model = model

    def emit(self, record):
        """ Write the log record message to the model.

        Use Html encoding to add colors, etc.

        """
        # TODO add coloring. Better to create a custom formatter
        try:
            msg = self.format(record)
            if record.levelname == 'INFO':
                deferred_call(self.model.add_message, msg + '\n')
            elif record.levelname == 'CRITICAL':
                deferred_call(self.model.add_message, ERR_MESS + '\n')
            else:
                deferred_call(self.model.add_message,
                              record.levelname + ': ' + msg + '\n')
        except Exception:
            pass


class DayRotatingTimeHandler(TimedRotatingFileHandler):
    """ Custom implementation of the TimeRotatingHandler to avoid issues on
    win32.

    Found on StackOverflow ...

    """
    def __init__(self, filename, mode='wb', **kwargs):
        self.mode = mode
        super(DayRotatingTimeHandler, self).__init__(filename, when='MIDNIGHT',
                                                     **kwargs)

    def _open(self):
        """Open a file named accordingly to the base name and the time of
        creation of the file with the (original) mode and encoding.

        """
        today = str(datetime.date.today())

        base_dir, base_filename = os.path.split(self.baseFilename)
        aux = base_filename.split('.')

        # Change filename when the logging system start several time on the
        # same day.
        i = 0
        filename = aux[0] + today + '_%d' + '.' + aux[1]
        while os.path.isfile(os.path.join(base_dir, filename % i)):
            i += 1

        path = os.path.join(base_dir, filename % i)

        if self.encoding is None:
            stream = open(path, self.mode)
        else:
            stream = codecs.open(path, self.mode, self.encoding)
        return stream

    def doRollover(self):
        """Do a rollover.

        Close old file and open a new one, no renaming is performed to avoid
        issues on window.

        """
        if self.stream:
            self.stream.close()
            self.stream = None
        # get the time that this sequence started at and make it a TimeTuple
        current_time = int(time.time())
        dst_now = time.localtime(current_time)[-1]

        self.stream = self._open()

        new_rollover_at = self.computeRollover(current_time)
        while new_rollover_at <= current_time:
            new_rollover_at = new_rollover_at + self.interval
        # If DST changes and midnight or weekly rollover, adjust for this.
        if ((self.when == 'MIDNIGHT' or self.when.startswith('W')) and
                not self.utc):
            dst_at_rollover = time.localtime(new_rollover_at)[-1]
            if dst_now != dst_at_rollover:
                # DST kicks in before next rollover, so we need to deduct an
                # hour
                if not dst_now:
                    addend = -3600
                # DST bows out before next rollover, so we need to add an hour
                else:
                    addend = 3600
                new_rollover_at += addend
        self.rolloverAt = new_rollover_at
