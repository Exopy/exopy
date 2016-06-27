# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Thread safe object to use in tasks.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
import threading
from multiprocessing import Event
from time import sleep

from atom.api import Unicode, set_default
from enaml.application import deferred_call

from ecpy.tasks.tasks.base_tasks import RootTask, ComplexTask
from ecpy.tasks.tasks.validators import Feval, SkipEmpty

from ecpy.testing.tasks.util import CheckTask, ExceptionTask
from ecpy.testing.util import process_app_events


class TestTaskExecution(object):
    """Test the execution of a hierarchy of tasks.

    """

    def setup(self):
        root = RootTask()
        root.should_pause = Event()
        root.should_stop = Event()
        root.paused = Event()
        root.resumed = Event()
        root.default_path = 'toto'
        self.root = root

    def test_check_simple_task(self, tmpdir):
        """Test automatic testing of formatting and evaluating.

        """
        class Tester(CheckTask):
            """Class declaring a member to format and one to eval.

            """
            form = Unicode().tag(fmt=True)

            feval = Unicode().tag(feval=Feval())

            feval_warn = Unicode().tag(feval=Feval(warn=True))

            feval_empty = Unicode().tag(feval=SkipEmpty())

            database_entries = set_default({'form': '', 'feval': 0,
                                            'feval_warn': 0, 'feval_empty': 0})

        tester = Tester(name='test', form='{default_path}',
                        feval='2*{test_val}', feval_warn='{test_val}',
                        feval_empty='{test_val}',
                        database_entries={'val': 1, 'form': '', 'feval': 0,
                                          'feval_warn': 0, 'feval_empty': 0})
        self.root.default_path = str(tmpdir)
        self.root.add_child_task(0, tester)

        res, tb = self.root.check()
        assert res and tb == {}
        assert self.root.get_from_database('test_form') == str(tmpdir)
        assert self.root.get_from_database('test_feval') == 2
        assert self.root.get_from_database('test_feval_warn') == 1
        assert self.root.get_from_database('test_feval_empty') == 1

        tester.feval_empty = ''
        res, tb = self.root.check()
        assert res and tb == {}

        tester.feval_warn = '**'
        res, tb = self.root.check()
        assert res
        assert 'root/test-feval_warn' in tb

        tester.form = '{test}'
        res, tb = self.root.check()
        assert not res and 'root/test-form' in tb

        tester.form = '{default_path}'
        tester.feval = '2*{test_val}*'
        res, tb = self.root.check()
        assert not res and 'root/test-feval' in tb

    def test_check_handle_wrong_feval(self, tmpdir):
        """Test handling the wrong type of feval value.

        """
        class Tester(CheckTask):
            """Class declaring a member to eval with the wrong kind of
            validator.

            """
            feval = Unicode().tag(feval=object())

        tester = Tester(name='test', feval='2*{test_val}',
                        database_entries={'val': 1, 'feval': 0})
        self.root.default_path = str(tmpdir)
        self.root.add_child_task(0, tester)
        res, tb = self.root.check()
        assert not res

    def test_check_complex_task(self, tmpdir):
        """Check handlign an exception occuring while running the checks.

        """
        class Tester(CheckTask):
            """Class declaring a member to format and one to eval.

            """
            def check(self, *args, **kwargs):
                raise Exception()

        tester = Tester(name='test')

        self.root.default_path = str(tmpdir)
        self.root.add_child_task(0, tester)

        res, tb = self.root.check()
        assert not res
        assert 'root/test' in tb

    @pytest.mark.timeout(10)
    def test_root_perform_empty(self):
        """Test running an empty RootTask.

        """
        root = self.root
        root.check()
        root.perform()

        assert not root.should_pause.is_set()
        assert not root.should_stop.is_set()

    @pytest.mark.timeout(10)
    def test_root_perform_exc(self):
        """Test handling a child raising an exception.

        """
        root = self.root
        root.add_child_task(0, ExceptionTask())
        root.check()
        root.perform()

        assert not root.should_pause.is_set()
        assert root.should_stop.is_set()

    @pytest.mark.timeout(10)
    def test_root_perform_simple(self):
        """Test running a simple task.

        """
        root = self.root
        aux = CheckTask(name='test')
        root.add_child_task(0, aux)
        root.check()
        root.perform()

        assert not root.should_pause.is_set()
        assert not root.should_stop.is_set()
        assert aux.perform_called == 1

    @pytest.mark.timeout(10)
    def test_root_perform_complex(self):
        """Test running a simple task.

        """
        root = self.root
        task = ComplexTask(name='comp')
        aux = CheckTask(name='test')
        root.add_child_task(0, task)
        task.add_child_task(0, aux)
        root.check()
        root.perform()

        assert not root.should_pause.is_set()
        assert not root.should_stop.is_set()
        assert aux.perform_called == 1

    @pytest.mark.timeout(10)
    def test_root_perform_parallel(self):
        """Test running a simple task in parallel.

        """
        main = threading.current_thread().name

        def thread_checker(task, value):
            """Check that this is not running in the main thread.

            """
            assert threading.current_thread().name != main

        root = self.root
        aux = CheckTask(name='test', custom=thread_checker)
        aux.parallel = {'activated': True, 'pool': 'test'}
        root.add_child_task(0, aux)
        root.add_child_task(1, CheckTask())
        root.check()
        root.perform()

        assert not root.should_pause.is_set()
        assert not root.should_stop.is_set()
        assert aux.perform_called == 1
        assert root.resources['threads']['test']

    def test_handle_task_exception_in_thread(self):
        """Test handling an exception occuring in a thread (test smooth_crash).

        """
        def raiser(task, value):
            raise Exception

        root = self.root
        aux = CheckTask(name='test', custom=raiser)
        aux.parallel = {'activated': True, 'pool': 'test'}
        root.add_child_task(0, aux)
        root.add_child_task(1, CheckTask())
        root.check()
        root.perform()

        assert not root.should_pause.is_set()
        assert root.should_stop.is_set()
        assert aux.perform_called == 1

    @pytest.mark.timeout(10)
    def test_root_perform_wait_all(self):
        """Test running a simple task waiting on all pools.

        """
        root = self.root

        event1 = threading.Event()
        event2 = threading.Event()

        par = CheckTask(name='test', custom=lambda t, x: event1.wait())
        par.parallel = {'activated': True, 'pool': 'test'}
        aux = CheckTask(name='signal', custom=lambda t, x: event2.set())
        wait = CheckTask(name='wait')
        wait.wait = {'activated': True}
        root.add_child_task(0, par)
        root.add_child_task(1, aux)
        root.add_child_task(2, wait)
        root.check()

        t = threading.Thread(target=root.perform)
        t.start()
        event2.wait()
        event1.set()
        t.join()

        assert not root.should_pause.is_set()
        assert not root.should_stop.is_set()
        assert par.perform_called == 1
        assert aux.perform_called == 1
        assert wait.perform_called == 1
        assert not root.resources['threads']['test']

    @pytest.mark.timeout(10)
    def test_root_perform_wait_single(self):
        """Test running a simple task waiting on a single pool.

        """
        root = self.root
        event1 = threading.Event()
        event2 = threading.Event()

        par = CheckTask(name='test', custom=lambda t, x: event1.wait())
        par.parallel = {'activated': True, 'pool': 'test'}
        aux = CheckTask(name='signal', custom=lambda t, x: event2.set())
        aux.parallel = {'activated': True, 'pool': 'aux'}
        wait = CheckTask(name='wait')
        wait.wait = {'activated': True, 'no_wait': ['aux']}
        root.add_child_task(0, par)
        root.add_child_task(1, aux)
        root.add_child_task(2, wait)
        root.check()

        t = threading.Thread(target=root.perform)
        t.start()
        event2.wait()
        event1.set()
        t.join()

        assert not root.should_pause.is_set()
        assert not root.should_stop.is_set()
        assert par.perform_called == 1
        assert aux.perform_called == 1
        assert wait.perform_called == 1
        assert not root.resources['threads']['test']
        assert root.resources['threads']['aux']

    @pytest.mark.timeout(10)
    def test_root_perform_no_wait_single(self):
        """Test running a simple task not waiting on a single pool.

        """
        root = self.root
        event1 = threading.Event()
        event2 = threading.Event()

        par = CheckTask(name='test', custom=lambda t, x: event1.wait())
        par.parallel = {'activated': True, 'pool': 'test'}
        aux = CheckTask(name='signal', custom=lambda t, x: event2.set())
        aux.parallel = {'activated': True, 'pool': 'aux'}
        wait = CheckTask(name='wait')
        wait.wait = {'activated': True, 'wait': ['test']}
        root.add_child_task(0, par)
        root.add_child_task(1, aux)
        root.add_child_task(2, wait)
        root.check()

        t = threading.Thread(target=root.perform)
        t.start()
        event2.wait()
        event1.set()
        t.join()

        assert not root.should_pause.is_set()
        assert not root.should_stop.is_set()
        assert par.perform_called == 1
        assert aux.perform_called == 1
        assert wait.perform_called == 1
        assert not root.resources['threads']['test']
        assert root.resources['threads']['aux']

    @pytest.mark.timeout(10)
    def test_stop(self):
        """Test stopping the execution.

        """
        root = self.root
        par = CheckTask(name='test',
                        custom=lambda t, x: t.root.should_stop.set())
        par2 = CheckTask(name='test2')
        for i, c in enumerate([par, par2]):
            root.add_child_task(i, c)
        root.check()
        root.perform()

        assert par.perform_called == 1
        assert not par2.perform_called

    @pytest.mark.timeout(10)
    def test_stop_unstoppable(self):
        """Try stopping unstoppable task.

        """
        root = self.root
        par = CheckTask(name='test',
                        custom=lambda t, x: t.root.should_stop.set())
        par2 = CheckTask(name='test2', stoppable=False)
        for i, c in enumerate([par, par2]):
            root.add_child_task(i, c)
        root.check()
        root.perform()

        assert par.perform_called == 1
        assert par2.perform_called == 1

    @pytest.mark.timeout(10)
    def test_pause1(self, app):
        """Test pausing and resuming the execution. (add instrs)

        Tricky as only the main thread is allowed to resume.

        """
        class Dummy(object):
            """False instrument checking that restarting does its job.

            """
            owner = 'test'
            called = 0

            def finalize(self):
                pass

            def clear_cache(self):
                self.called += 1

        class Starter(object):
            """False instrument starter.

            """
            def reset(self, driver):
                driver.clear_cache()
                driver.owner = ''

            def stop(self, driver):
                driver.stop()

        def pause(task, value):
            """Post a method restarting execution on event loop and pause.

            """
            deferred_call(lambda t: t.root.should_pause.clear(), task)
            task.root.should_pause.set()

        root = self.root
        dummy = Dummy()
        root.resources['instrs']['test'] = dummy, Starter()
        par = CheckTask(name='test', custom=pause)
        comp = ComplexTask(name='comp', stoppable=False,
                           parallel={'activated': True, 'pool': 'test'})
        par2 = CheckTask(name='test2')
        comp.add_child_task(0, par2)
        par3 = CheckTask(name='test3')
        for i, c in enumerate([par, comp, par3]):
            root.add_child_task(i, c)
        root.check()

        t = threading.Thread(target=root.perform)
        t.start()
        sleep(0.1)
        process_app_events()
        t.join()

        assert not root.should_pause.is_set()
        assert not root.should_stop.is_set()
        assert par.perform_called == 1
        assert par2.perform_called == 1
        assert par3.perform_called == 1
        assert root.resumed.is_set()
        assert dummy.called == 1
        assert dummy.owner == ''

    @pytest.mark.timeout(10)
    def test_pause2(self, app):
        """Test pausing and stopping the execution.

        """
        def pause_and_stop(task, value):
            """Post a method stopping execution on event loop and pause.

            """
            deferred_call(lambda t: t.root.should_stop.set(), task)
            task.root.should_pause.set()

        root = self.root
        par = CheckTask(name='test', custom=pause_and_stop)
        comp = ComplexTask(name='comp', stoppable=False,
                           parallel={'activated': True, 'pool': 'test'})
        par2 = CheckTask(name='test2')
        comp.add_child_task(0, par2)
        par3 = CheckTask(name='test3')
        for i, c in enumerate([par, comp, par3]):
            root.add_child_task(i, c)
        root.check()

        t = threading.Thread(target=root.perform)
        t.start()
        sleep(0.1)
        process_app_events()
        t.join()

        assert root.should_pause.is_set()
        assert root.should_stop.is_set()
        assert par.perform_called
        assert not par2.perform_called
        assert not par3.perform_called

    def test_handle_finalisation_issues(self):
        """Test the handling of issues in cleaning ressources in root.

        """
        class FalseThread(object):
            """False thread which cannot be joined.

            """
            called = 0

            def join(self):
                self.called += 1
                raise Exception()

        class FalseInstr(object):
            """False instr which cannot be finalized.

            """
            called = 0

            def finalize(self):
                self.called += 1
                raise Exception()

        class FalseStarter(object):
            """False instrument starter.

            """

            def stop(self, driver):
                driver.stop()

        class FalseFile(object):
            """False file which cannot be closed.

            """
            called = 0

            def close(self):
                self.called += 1
                raise Exception()

        root = self.root
        thread = FalseThread()
        root.resources['threads']['test'] = [thread]
        instr = FalseInstr()
        root.resources['instrs']['a'] = instr, FalseStarter()
        stream = FalseFile()
        root.resources['files']['b'] = stream

        root.perform()

        assert thread.called == 1
        assert instr.called == 1
        assert stream.called == 1
