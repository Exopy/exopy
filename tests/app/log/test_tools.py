# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the logging tools.

"""
import sys
from multiprocessing import Queue
from time import sleep, localtime
from exopy.app.log.tools import (StreamToLogRedirector, QueueHandler,
                                 LogModel, DayRotatingTimeHandler,
                                 GuiHandler, QueueLoggerThread)


def test_log_model():
    """Test the log model buff_size handling.

    """
    model = LogModel(buff_size=4)
    for i in range(5):
        model.add_message('%d\n' % i)

    check = ''.join(['%d\n' % i for i in range(5)])
    assert model.text == check
    model.add_message('%d' % 5)
    assert model.text == check.partition('\n')[-1] + '%d\n' % 5

    model.clean_text()
    for i in range(4):
        model.add_message('%d\n' % i)
    assert model.text == ''.join(['%d\n' % i for i in range(4)])


def test_gui_handler(exopy_qtbot, logger, monkeypatch):
    """Test the gui handler.

    """
    model = LogModel()
    handler = GuiHandler(model)
    logger.addHandler(handler)

    logger.info('test')

    def assert_text():
        assert model.text == 'test\n'
    exopy_qtbot.wait_until(assert_text)
    model.clean_text()

    logger.debug('test')

    def assert_text():
        assert model.text == 'DEBUG: test\n'
    exopy_qtbot.wait_until(assert_text)
    model.clean_text()

    logger.warn('test')

    def assert_text():
        assert model.text == 'WARNING: test\n'
    exopy_qtbot.wait_until(assert_text)
    model.clean_text()

    logger.error('test')

    def assert_text():
        assert model.text == 'ERROR: test\n'
    exopy_qtbot.wait_until(assert_text)
    model.clean_text()

    logger.critical('test')
    answer = 'An error occured please check the log file for more details.\n'

    def assert_text():
        assert model.text == answer
    exopy_qtbot.wait_until(assert_text)
    model.clean_text()

    def err(record):
        raise Exception

    monkeypatch.setattr(handler, 'format', err)
    logger.info('raise')


def test_stdout_redirection(exopy_qtbot, logger):
    """Test the redirection of stdout toward a logger.

    """
    model = LogModel()
    handler = GuiHandler(model)
    logger.addHandler(handler)
    stdout = sys.stdout
    sys.stdout = StreamToLogRedirector(logger)

    try:
        print('test')
        sys.stdout.flush()
    finally:
        sys.stdout = stdout

    def assert_text():
        assert model.text == 'test\n'
    exopy_qtbot.wait_until(assert_text)


def test_stderr_redirection(exopy_qtbot, logger):
    """Test the redirection of 'stderr' toward a logger.

    """
    model = LogModel()
    handler = GuiHandler(model)
    logger.addHandler(handler)
    stdout = sys.stdout
    sys.stdout = StreamToLogRedirector(logger, stream_type='stderr')

    try:
        print('test')
    finally:
        sys.stdout = stdout

    answer = 'An error occured please check the log file for more details.\n'

    def assert_text():
        assert model.text == answer
    exopy_qtbot.wait_until(assert_text)


def test_queue_handler(logger, monkeypatch):
    """Test the queue handler.

    """
    queue = Queue()
    handler = QueueHandler(queue)
    logger.addHandler(handler)
    logger.info('test')

    record = queue.get(timeout=1.0)
    assert record.message == 'test'

    def err(record):
        raise Exception()

    monkeypatch.setattr(handler, 'enqueue', err)
    logger.info('raise')


def test_logger_thread(exopy_qtbot, logger):
    """Test the logger thread.

    """
    queue = Queue()
    handler = QueueHandler(queue)
    logger.addHandler(handler)
    logger.info('test')
    logger.removeHandler(handler)

    model = LogModel()
    handler = GuiHandler(model)
    logger.addHandler(handler)

    thread = QueueLoggerThread(queue)
    thread.start()
    sleep(1)
    queue.put(None)
    thread.join(2)

    if thread.is_alive():
        raise RuntimeError()

    def assert_text():
        assert model.text == 'test\n'
    exopy_qtbot.wait_until(assert_text)


def test_rotating_file_handler(tmpdir, logger, monkeypatch):
    """Test the rotating file handler.

    """
    def rollover(obj, current_time):
        return current_time + 0.1

    monkeypatch.setattr(DayRotatingTimeHandler, 'computeRollover', rollover)
    handler = DayRotatingTimeHandler(str(tmpdir.join('test.log')))
    logger.addHandler(handler)

    logger.info('test')
    sleep(1)
    logger.info('test')

    assert len(tmpdir.listdir()) == 2


def test_rotating_file_handler_encoded(tmpdir, logger, monkeypatch):
    """Test the rotating file handler with an encoding.

    Test always pass by increase coverage.

    """
    def rollover(obj, current_time):
        return current_time + 0.1

    monkeypatch.setattr(DayRotatingTimeHandler, 'computeRollover', rollover)
    handler = DayRotatingTimeHandler(str(tmpdir.join('test.log')),
                                     encoding='utf8')
    logger.addHandler(handler)

    logger.info('test')
    sleep(1)
    logger.info('test')

    assert len(tmpdir.listdir()) == 2


def test_rotating_file_handler_interval(tmpdir, logger, monkeypatch):
    """Test the rotating file handler when the rollover return a time smaller
    than the current time.

    """
    def rollover(obj, current_time):
        return current_time - 0.1

    monkeypatch.setattr(DayRotatingTimeHandler, 'computeRollover', rollover)
    handler = DayRotatingTimeHandler(str(tmpdir.join('test.log')))
    handler.interval = 0.2
    logger.addHandler(handler)

    # Probably because we gives a negative time.
    assert len(tmpdir.listdir()) == 1

    logger.info('test')
    sleep(1)
    logger.info('test')

    assert len(tmpdir.listdir()) == 3


def test_rotating_file_handler_dst(tmpdir, logger, monkeypatch):
    """Test the rotating file handler when dst change.

    """
    class Aux(object):
        counter = 0

        @classmethod
        def loct(cls, t):
            """Change DST at each call.

            """
            t = list(localtime(t))
            t[-1] = cls.counter % 2
            cls.counter += 1
            return t

    def rollover(obj, current_time):
        return current_time + 0.1

    monkeypatch.setattr(DayRotatingTimeHandler, 'computeRollover', rollover)
    from exopy.app.log.tools import time
    monkeypatch.setattr(time, 'localtime', Aux.loct)
    handler = DayRotatingTimeHandler(str(tmpdir.join('test.log')))
    logger.addHandler(handler)

    # Force a first rollover.
    handler.rolloverAt = int(time.time())
    t = int(time.time())
    logger.info('test')
    assert abs(handler.rolloverAt - t + 3600) < 1

    handler.rolloverAt = int(time.time())
    t = int(time.time())
    time.localtime(t)
    logger.info('test')
    assert abs(handler.rolloverAt - t - 3600) < 1
