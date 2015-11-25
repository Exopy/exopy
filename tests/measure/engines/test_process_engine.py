# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test process engine functionalities.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import socket
from threading import Thread
from time import sleep

import pytest
import enaml
from atom.api import Value, Bool, Unicode
from future.builtins import str as text

from ecpy.measure.engines.api import ExecutionInfos
from ecpy.tasks.api import RootTask, SimpleTask
from ecpy.tasks.manager.infos import TaskInfos
from ecpy.measure.engines.process_engine.subprocess import TaskProcess

from ecpy.testing.util import process_app_events

with enaml.imports():
    from ecpy.measure.engines.process_engine.engine_declaration import\
        ProcFilter
    from ecpy.app.log.manifest import LogManifest
    from ecpy.tasks.manager.manifest import TasksManagerManifest


pytest_plugins = str('ecpy.testing.measure.workspace.fixtures'),


class WaitingTask(SimpleTask):
    """Simple Task whose execution can be controlled using events.

    """
    check_flag = Bool(True).tag(pref=True)
    sync_port = Value(()).tag(pref=True)
    sock_id = Unicode().tag(pref=True)

    def check(self, *args, **kwargs):
        super(WaitingTask, self).check(*args, **kwargs)
        return self.check_flag, {'test': 1}

    def perform(self):
        s = socket.socket()
        while True:
            if s.connect_ex(('localhost', self.sync_port)) == 0:
                break
            sleep(0.01)
        s.sendall(self.sock_id.encode('utf-8'))
        s.recv(4096)
        s.sendall('Waiting'.encode('utf-8'))
        s.recv(4096)
        s.close()


class ExecThread(Thread):
    """Thread storing the return value of the engine perform method.

    """
    def __init__(self, engine, exec_infos):
        super(ExecThread, self).__init__()
        self._engine = engine
        self._exec_infos = exec_infos
        self.value = None

    def run(self):
        self.value = self._engine.perform(self._exec_infos)


@pytest.fixture
def process_engine(measure_workbench):
    measure_workbench.register(LogManifest())
    measure_workbench.register(TasksManagerManifest())
    plugin = measure_workbench.get_plugin('ecpy.measure')
    return plugin.create('engine', 'ecpy.process_engine')


@pytest.yield_fixture
def sync_server():
    class SyncServer(object):

        timeout = 10

        def __init__(self):
            self._sock = socket.socket()
            self._sock.bind(('localhost', 0))
            self._sock.settimeout(self.timeout)
            self.port = self._sock.getsockname()[1]
            self._received = []
            self._answer_pipes = {}

        def wait(self, sock_id):
            """Wait for a given socket to send a message

            """
            if sock_id in self._received:
                del self._received[self._received.index(sock_id)]
                return

            if sock_id not in self._answer_pipes:
                self._sock.listen(5)
                sock, _ = self._sock.accept()
                sock.settimeout(self.timeout)
                s_id = sock.recv(4096).decode('utf-8')
                if sock_id != s_id:
                    raise RuntimeError('%s != %s' % (sock_id, s_id))
                sock.sendall('OK')
                self._answer_pipes[sock_id] = sock

            self._answer_pipes[sock_id].recv(4096).decode('utf-8')

        def signal(self, sock_id):
            """Send a message to the specifed socket.

            The socket must first have been waited on.

            """
            self._answer_pipes[sock_id].sendall('Go'.encode('utf-8'))

        def reset(self):
            """Clean up internals.

            """
            self._received = []
            self._answer_pipes.clear()

    sync = SyncServer()

    yield sync

    sync._sock.close()


@pytest.fixture
def exec_infos(measure_workbench, measure, tmpdir, process_engine,
               sync_server):

    tp = measure_workbench.get_plugin('ecpy.tasks')
    tp._tasks.contributions['tests.WaitingTask'] = TaskInfos(cls=WaitingTask)

    r = RootTask(default_path=text(tmpdir))
    r.add_child_task(0, WaitingTask(name='test1', sock_id='test1',
                                    sync_port=sync_server.port))
    r.add_child_task(1, WaitingTask(name='test2', sock_id='test2',
                                    sync_port=sync_server.port))

    measure.root_task = r
    deps = measure.dependencies
    res, msg, errors = deps.collect_runtimes()
    assert res

    return ExecutionInfos(
            id='test',
            task=r,
            build_deps=deps.get_build_dependencies().dependencies,
            runtime_deps=deps.get_runtime_dependencies('main'),
            observed_entries=['test'],
            checks=not measure.forced_enqueued,
            )


def test_proc_filter():
    """Test the filter for the logging.

    """
    class FalseRecord(object):
        def __init__(self, processName):
            self.processName = processName

    f = ProcFilter(process_name='test', reject_if_equal=False)
    assert f.filter(FalseRecord('test'))
    assert not f.filter(FalseRecord('test2'))

    f = ProcFilter(process_name='test', reject_if_equal=True)
    assert not f.filter(FalseRecord('test'))
    assert f.filter(FalseRecord('test2'))


def test_workspace_contribution(workspace):
    """Test that the Process engine contribute correctly to the workspace
    when selected.

    """
    workspace.plugin.selected_engine = 'ecpy.process_engine'
    process_app_events()
    assert workspace.dock_area.find('ecpy.subprocess_log')

    log = workspace.plugin.workbench.get_plugin('ecpy.app.logging')
    assert 'ecpy.measure.engines.process_engine' in log.handler_ids
    assert 'ecpy.measure.engines.process_engine' in log.filter_ids
    assert 'ecpy.measure.workspace.process_engine' in log.filter_ids

    workspace.plugin.selected_engine = ''
    process_app_events()
    assert not workspace.dock_area.find('ecpy.subprocess_log')


@pytest.mark.timeout(30)
def test_perform(process_engine, exec_infos, sync_server):
    """Test perfoming a task.

    """
    exec_infos.observed_entries = ['test']
    t = ExecThread(process_engine, exec_infos)
    t.start()
    sync_server.wait('test1')
    sync_server.signal('test1')
    sync_server.wait('test2')
    sync_server.signal('test2')
    t.join()
    assert t.value.success
    assert not t.value.errors
    assert process_engine.status == 'Waiting'

    sync_server.reset()
    t = ExecThread(process_engine, exec_infos)
    t.start()
    sync_server.wait('test1')
    sync_server.signal('test1')
    sync_server.wait('test2')
    sync_server.signal('test2')
    t.join()
    assert t.value.success
    assert process_engine.status == 'Waiting'

    process_engine.shutdown()
    while not process_engine.status == 'Stopped':
        sleep(0.01)


@pytest.mark.timeout(30)
def test_handle_fail_check(process_engine, exec_infos):
    """Test handling a measure failing the checks.

    """
    t = ExecThread(process_engine, exec_infos)
    exec_infos.task.children[0].check_flag = False
    t.start()
    t.join()
    assert not t.value.success
    assert 'test' in t.value.errors
    assert process_engine.status == 'Waiting'

    process_engine.shutdown()
    while not process_engine.status == 'Stopped':
        sleep(0.01)


@pytest.mark.timeout(30)
def test_skipping_checks(process_engine, exec_infos, sync_server):
    """Test skipping a task checks.

    """
    t = ExecThread(process_engine, exec_infos)
    exec_infos.task.children[0].check_flag = False
    exec_infos.checks = False
    t.start()
    sync_server.wait('test1')
    sync_server.signal('test1')
    sync_server.wait('test2')
    sync_server.signal('test2')
    t.join()
    assert t.value.success
    assert process_engine.status == 'Waiting'

    process_engine.shutdown()
    while not process_engine.status == 'Stopped':
        sleep(0.01)


class DummyP(TaskProcess):
    def run(self):
        pass


@pytest.mark.timeout(30)
def test_handling_unpected_death_of_subprocess(process_engine, exec_infos,
                                               monkeypatch):
    """Test handling a death of the subprocess at startup.

    """
    from ecpy.measure.engines.process_engine import engine

    monkeypatch.setattr(engine, 'TaskProcess', DummyP)
    t = ExecThread(process_engine, exec_infos)
    exec_infos.task.children[0].check_flag = False
    t.start()
    t.join()
    assert not t.value.success
    assert 'engine' in t.value.errors
    assert 'dead' in t.value.errors['engine']
    assert process_engine.status == 'Stopped'


class DummyP1(TaskProcess):
    def run(self):
        self.pipe.recv()
        self.pipe.close()


@pytest.mark.timeout(30)
def test_handling_unexpected_closing_of_pipe1(process_engine, exec_infos,
                                              monkeypatch):
    """Test handling pipe closing while expecting answer after sending task.

    """
    from ecpy.measure.engines.process_engine import engine

    monkeypatch.setattr(engine, 'TaskProcess', DummyP1)
    t = ExecThread(process_engine, exec_infos)
    exec_infos.task.children[0].check_flag = False
    t.start()
    t.join()
    assert not t.value.success
    assert 'engine' in t.value.errors
    assert 'dead' in t.value.errors['engine']
    assert process_engine.status == 'Stopped'


class DummyP2(TaskProcess):
    def run(self):
        self.pipe.recv()
        self.pipe.send(True)
        self.pipe.close()


@pytest.mark.timeout(10)
def test_handling_unexpected_closing_of_pipe2(process_engine, exec_infos,
                                              monkeypatch):
    """Test handling pipe closing while expecting execution result.

    """
    from ecpy.measure.engines.process_engine import engine

    monkeypatch.setattr(engine, 'TaskProcess', DummyP2)
    t = ExecThread(process_engine, exec_infos)
    exec_infos.task.children[0].check_flag = False
    t.start()
    t.join()
    assert not t.value.success
    assert 'engine' in t.value.errors
    assert 'dead' in t.value.errors['engine']
    assert process_engine.status == 'Stopped'


def build_subprocess_infos(self, exec_infos):
    return ()


@pytest.mark.timeout(10)
def test_handling_unexpected_exception_in_sub_process(process_engine,
                                                      exec_infos,
                                                      monkeypatch):
    """Test handling pipe closing while expecting execution result.

    """
    from ecpy.measure.engines.process_engine import engine

    monkeypatch.setattr(engine.ProcessEngine, '_build_subprocess_args',
                        build_subprocess_infos)
    t = ExecThread(process_engine, exec_infos)
    exec_infos.task.children[0].check_flag = False
    t.start()
    t.join()
    assert not t.value.success
    assert 'engine' in t.value.errors
    assert 'dead' in t.value.errors['engine']
    assert process_engine.status == 'Stopped'


@pytest.mark.timeout(30)
def test_pause_resume(process_engine, exec_infos, sync_server):
    """Test pausing a measure.

    """
    t = ExecThread(process_engine, exec_infos)
    t.start()
    sync_server.wait('test1')
    process_engine.pause()
    assert process_engine.status == 'Pausing'

    sync_server.signal('test1')
    i = 0
    while not process_engine.status == 'Paused':
        i += 1
        sleep(0.01)
        if i > 2000:
            raise RuntimeError()

    process_engine.resume()
    sync_server.wait('test2')
    assert process_engine.status == 'Running'

    sync_server.signal('test2')
    t.join()
    assert t.value.success
    assert process_engine.status == 'Waiting'

    process_engine.shutdown()
    while not process_engine.status == 'Stopped':
        sleep(0.01)


@pytest.mark.timeout(30)
def test_pause_stop(process_engine, exec_infos, sync_server):
    """Test pausing a measure and stopping during the pause.

    """
    t = ExecThread(process_engine, exec_infos)
    t.start()
    sync_server.wait('test1')
    process_engine.pause()
    assert process_engine.status == 'Pausing'

    sync_server.signal('test1')
    i = 0
    while not process_engine.status == 'Paused':
        i += 1
        sleep(0.01)
        if i > 2000:
            raise RuntimeError()

    process_engine.stop()
    t.join()
    assert not t.value.success
    assert process_engine.status == 'Waiting'


@pytest.mark.timeout(30)
def test_stop(process_engine, exec_infos, sync_server):
    """Test stopping a measure in the middle.

    """
    t = ExecThread(process_engine, exec_infos)
    t.start()
    sync_server.wait('test1')
    process_engine.stop()
    sync_server.signal('test1')
    t.join()
    assert not t.value.success
    assert process_engine.status == 'Waiting'

    process_engine.shutdown()
    while not process_engine.status == 'Stopped':
        sleep(0.01)


@pytest.mark.timeout(30)
def test_force_stop(process_engine, exec_infos, sync_server):
    """Test forcing the stop of the engine.

    """
    t = ExecThread(process_engine, exec_infos)
    t.start()
    sync_server.wait('test1')
    process_engine.stop(force=True)
    t.join()
    assert 'engine' in t.value.errors
    assert 'terminated' in t.value.errors['engine']
    assert process_engine.status == 'Stopped'


@pytest.mark.timeout(30)
def test_shutdown(process_engine, exec_infos, sync_server):
    """Test shutting down the engine during the execution.

    """
    t = ExecThread(process_engine, exec_infos)
    t.start()
    sync_server.wait('test1')
    process_engine.shutdown()
    sync_server.signal('test1')
    t.join()

    while not process_engine.status == 'Stopped':
        sleep(0.01)


@pytest.mark.timeout(30)
def test_force_shutdown(process_engine, exec_infos, sync_server):
    """Test forcing the shutdown of the engine.

    """
    t = ExecThread(process_engine, exec_infos)
    t.start()
    sync_server.wait('test1')
    process_engine.shutdown(force=True)
    t.join()
    assert 'engine' in t.value.errors
    assert 'terminated' in t.value.errors['engine']
    assert process_engine.status == 'Stopped'
