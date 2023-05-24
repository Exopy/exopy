# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""test execution of tasks.

"""
import gc
import os
import threading
from multiprocessing import Event
from time import sleep

import pytest
from atom.api import Str, set_default
from enaml.application import deferred_call

from exopy.tasks.tasks.base_tasks import RootTask, ComplexTask
from exopy.tasks.tasks.validators import Feval, SkipEmpty

from exopy.testing.tasks.util import CheckTask, ExceptionTask


class TestTaskExecution(object):
    """Test the execution of a hierarchy of tasks.

    """

    def setup_method(self):
        root = RootTask()
        root.should_pause = Event()
        root.should_stop = Event()
        root.paused = Event()
        root.resumed = Event()
        root.default_path = 'toto'
        root.write_in_database('meas_name', 'M')
        root.write_in_database('meas_id', '001')
        self.root = root

    def teardown_method(self):
        del self.root.should_pause
        del self.root.should_stop
        del self.root.paused
        del self.root.resumed
        # Ensure we collect the file descriptor of the events. Otherwise we can
        # get funny errors on MacOS.
        gc.collect()

    def test_check_simple_task(self, tmpdir):
        """Test automatic testing of formatting and evaluating.

        """
        class Tester(CheckTask):
            """Class declaring a member to format and one to eval.

            """
            form = Str().tag(fmt=True)

            feval = Str().tag(feval=Feval())

            feval_warn = Str().tag(feval=Feval(warn=True))

            feval_empty = Str().tag(feval=SkipEmpty())

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
            feval = Str().tag(feval=object())

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
        root.perform()

        assert not root.should_pause.is_set()
        assert not root.should_stop.is_set()

    @pytest.mark.timeout(10)
    def test_root_perform_exc(self):
        """Test handling a child raising an exception.

        """
        root = self.root
        root.add_child_task(0, ExceptionTask())
        assert root.perform() is False

        assert not root.should_pause.is_set()
        assert root.should_stop.is_set()
        assert root.errors

    @pytest.mark.timeout(10)
    def test_root_perform_simple(self):
        """Test running a simple task.

        """
        root = self.root
        aux = CheckTask(name='test')
        root.add_child_task(0, aux)
        root.perform()

        assert not root.should_pause.is_set()
        assert not root.should_stop.is_set()
        assert aux.perform_called == 1

    @pytest.mark.timeout(10)
    def test_root_perform_profile(self, tmpdir):
        """Test running a simple task.

        """
        self.root.default_path = str(tmpdir)
        root = self.root
        aux = CheckTask(name='test')
        root.add_child_task(0, aux)
        root.should_profile = True
        root.perform()

        assert not root.should_pause.is_set()
        assert not root.should_stop.is_set()
        assert aux.perform_called == 1

        meas_name = self.root.get_from_database('meas_name')
        meas_id = self.root.get_from_database('meas_id')
        path = os.path.join(self.root.default_path,
                            meas_name + '_' + meas_id + '.prof')
        assert os.path.isfile(path)

    @pytest.mark.timeout(10)
    def test_root_perform_complex(self):
        """Test running a simple task.

        """
        root = self.root
        task = ComplexTask(name='comp')
        aux = CheckTask(name='test')
        root.add_child_task(0, task)
        task.add_child_task(0, aux)
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
            assert task.root.resources['threads']['test']
            assert threading.current_thread().name != main

        root = self.root
        aux = CheckTask(name='test', custom=thread_checker)
        aux.parallel = {'activated': True, 'pool': 'test'}
        root.add_child_task(0, aux)
        root.add_child_task(1, CheckTask())
        root.perform()

        assert not root.should_pause.is_set()
        assert not root.should_stop.is_set()
        assert aux.perform_called == 1

    @pytest.mark.timeout(10)
    def test_root_perform_parallel_in_finalization(self):
        """Ensure that the ThreadResources release does not prevent to start
        new threads.

        """
        root = self.root

        event1 = threading.Event()
        event2 = threading.Event()
        event3 = threading.Event()

        comp = ComplexTask(name='comp')
        comp.parallel = {'activated': True, 'pool': 'test'}
        aux = CheckTask(name='signal', custom=lambda t, x: event1.set())
        wait = CheckTask(name='test', custom=lambda t, x: event2.wait())
        par = CheckTask(name='signal', custom=lambda t, x: event3.set())
        # Test creating a new thread as by priority active_threads is released
        # later.
        par.parallel = {'activated': True, 'pool': 'test2'}
        comp.add_child_task(0, aux)
        comp.add_child_task(1, wait)
        comp.add_child_task(2, par)
        root.add_child_task(0, comp)

        t = threading.Thread(target=root.perform)
        t.start()
        event1.wait()
        assert root.resources['active_threads']['test']
        assert not root.resources['active_threads']['test2']
        event2.set()
        event3.wait()
        t.join()

        assert not root.should_pause.is_set()
        assert not root.should_stop.is_set()
        assert par.perform_called == 1
        assert aux.perform_called == 1
        assert wait.perform_called == 1
        assert not root.resources['active_threads']['test']

    def test_handle_task_exception_in_thread(self):
        """Test handling an exception occuring in a thread (test smooth_crash).

        """
        def raiser(task, value):
            raise Exception()

        root = self.root
        aux = CheckTask(name='test', custom=raiser)
        aux.parallel = {'activated': True, 'pool': 'test'}
        root.add_child_task(0, aux)
        root.add_child_task(1, CheckTask())
        root.perform()

        assert not root.should_pause.is_set()
        assert root.should_stop.is_set()
        assert aux.perform_called == 1

    @pytest.mark.timeout(10)
    def test_root_perform_wait_all(self):
        """Test running a simple task waiting on all pools.

        Notes
        -----
        When starting par will be executed in its own thread, which will allow
        aux to run. The test will wait for aux to set its flag. At this step
        wait should be waiting as one pool is active. After checking that we
        can set the flag on which par is waiting and let the execution
        complete.

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

        t = threading.Thread(target=root.perform)
        t.start()
        event2.wait()
        sleep(1)
        assert not wait.perform_called
        assert root.resources['active_threads']['test']
        event1.set()
        t.join()

        assert not root.should_pause.is_set()
        assert not root.should_stop.is_set()
        assert par.perform_called == 1
        assert aux.perform_called == 1
        assert wait.perform_called == 1
        assert not root.resources['active_threads']['test']

    @pytest.mark.timeout(10)
    def test_root_perform_no_wait_single(self):
        """Test running a simple task waiting on a single pool.

        Notes
        -----
        When starting par will be executed in its own thread, which will allow
        par2 to start (also in its own thread) as a consequence aux will be
        run. The test will wait for aux to set its flag. At this step wait
        should be waiting as one pool other than test is active. After checking
        that, we set the flag on which par is waiting. This should allow wait
        to run. Once we have checked it is so, we let par2 complete.

        """
        root = self.root
        event1 = threading.Event()
        event2 = threading.Event()
        event3 = threading.Event()
        event4 = threading.Event()

        par = CheckTask(name='test', custom=lambda t, x: event1.wait())
        par.parallel = {'activated': True, 'pool': 'aux'}
        par2 = CheckTask(name='test', custom=lambda t, x: event2.wait())
        par2.parallel = {'activated': True, 'pool': 'test'}
        aux = CheckTask(name='signal', custom=lambda t, x: event3.set())
        wait = CheckTask(name='wait', custom=lambda t, x: event4.set())
        wait.wait = {'activated': True, 'no_wait': ['test']}
        root.add_child_task(0, par)
        root.add_child_task(1, par2)
        root.add_child_task(2, aux)
        root.add_child_task(3, wait)

        t = threading.Thread(target=root.perform)
        t.start()
        event3.wait()
        sleep(1)
        assert not wait.perform_called
        assert root.resources['active_threads']['test']
        assert root.resources['active_threads']['aux']
        event1.set()
        event4.wait()
        assert wait.perform_called
        assert root.resources['active_threads']._dict['test']
        assert not root.resources['active_threads']['aux']
        event2.set()
        t.join()

        assert not root.should_pause.is_set()
        assert not root.should_stop.is_set()
        assert par.perform_called == 1
        assert par2.perform_called == 1
        assert aux.perform_called == 1
        assert wait.perform_called == 1
        assert not root.resources['active_threads']['test']
        assert not root.resources['active_threads']['aux']

    @pytest.mark.timeout(20)
    def test_root_perform_wait_single(self):
        """Test running a simple task waiting on a single pool.

        Notes
        -----
        When starting par will be executed in its own thread, which will allow
        par2 to start (also in its own thread) as a consequence aux will be
        run. The test will wait for aux to set its flag. At this step wait
        should be waiting as one thread in test pool is active. After checking
        that, we set the flag on which par2 is waiting. This should allow wait
        to run. Once we have checked it is so, we let par complete.

        """
        root = self.root
        event1 = threading.Event()
        event2 = threading.Event()
        event3 = threading.Event()
        event4 = threading.Event()

        par = CheckTask(name='test', custom=lambda t, x: event1.wait())
        par.parallel = {'activated': True, 'pool': 'aux'}
        par2 = CheckTask(name='test', custom=lambda t, x: event2.wait())
        par2.parallel = {'activated': True, 'pool': 'test'}
        aux = CheckTask(name='signal', custom=lambda t, x: event3.set())
        wait = CheckTask(name='wait', custom=lambda t, x: event4.set())
        wait.wait = {'activated': True, 'wait': ['test']}
        root.add_child_task(0, par)
        root.add_child_task(1, par2)
        root.add_child_task(2, aux)
        root.add_child_task(3, wait)

        t = threading.Thread(target=root.perform)
        t.start()
        event3.wait()
        sleep(1)
        assert not wait.perform_called
        assert root.resources['active_threads']['test']
        assert root.resources['active_threads']['aux']
        event2.set()
        event4.wait()
        assert wait.perform_called
        assert root.resources['active_threads']['aux']
        assert not root.resources['active_threads']['test']
        event1.set()
        t.join()

        assert not root.should_pause.is_set()
        assert not root.should_stop.is_set()
        assert par.perform_called == 1
        assert par2.perform_called == 1
        assert aux.perform_called == 1
        assert wait.perform_called == 1
        assert not root.resources['active_threads']['test']
        assert not root.resources['active_threads']['aux']

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
        root.perform()

        assert par.perform_called == 1
        assert par2.perform_called == 1

    @pytest.mark.timeout(10)
    def test_pause1(self, exopy_qtbot):
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

        t = threading.Thread(target=root.perform)
        t.start()
        sleep(0.1)
        exopy_qtbot.wait(10)
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
    def test_pause2(self, exopy_qtbot):
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

        t = threading.Thread(target=root.perform)
        t.start()
        sleep(0.1)
        exopy_qtbot.wait(10)
        t.join()

        assert root.should_pause.is_set()
        assert root.should_stop.is_set()
        assert par.perform_called
        assert not par2.perform_called
        assert not par3.perform_called

    def test_handle_finalisation_issues(self):
        """Test the handling of issues in cleaning ressources in root.

        """
        release_order = []

        class FalseThreadDispatcher(object):
            """False thread which cannot be joined.

            """
            called = 0

            def stop(self):
                release_order.append(self)
                self.called += 1
                raise Exception()

        class FalseInstr(object):
            """False instr which cannot be finalized.

            """
            called = 0

            def finalize(self):
                self.called += 1
                release_order.append(self)
                raise Exception()

        class FalseStarter(object):
            """False instrument starter.

            """

            def stop(self, driver):
                driver.finalize()

        class FalseFile(object):
            """False file which cannot be closed.

            """
            called = 0

            def close(self):
                self.called += 1
                release_order.append(self)
                raise Exception()

        root = self.root
        thread = FalseThreadDispatcher()
        root.resources['threads']['test'] = [thread]
        instr = FalseInstr()
        root.resources['instrs']['a'] = instr, FalseStarter()
        stream = FalseFile()
        root.resources['files']['b'] = stream

        root.perform()

        assert thread.called == 1
        assert instr.called == 1
        assert stream.called == 1
        assert (release_order == [thread, instr, stream] or
                release_order == [thread, stream, instr])
