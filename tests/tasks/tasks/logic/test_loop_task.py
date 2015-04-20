# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test of the LoopTask.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
from multiprocessing import Event

from ecpy.tasks.api import RootTask
from ecpy.tasks.tasks.logic.loop_task import LoopTask
from ecpy.tasks.tasks.logic.loop_iterable_interface\
    import IterableLoopInterface
from ecpy.tasks.tasks.logic.loop_linspace_interface\
    import LinspaceLoopInterface
from ecpy.tasks.tasks.logic.loop_exceptions_tasks\
    import BreakTask, ContinueTask

from ...execution_testing import CheckTask


@pytest.fixture
def linspace_interface(request):
    """Fixture building a linspace interface.

    """
    interface = LinspaceLoopInterface()
    interface.start = '1.0'
    interface.stop = '2.0'
    interface.step = '0.1'
    return interface


@pytest.fixture
def iterable_interface(request):
    """Fixture building a linspace interface.

    """
    interface = IterableLoopInterface()
    interface.iterable = 'range(11)'
    return interface


class TestLoopTask(object):
    """Test Loop task with and without included child.

    """

    def setup(self):
        self.root = RootTask(should_stop=Event(), should_pause=Event())
        self.task = LoopTask(name='Test')
        self.root.add_child_task(0, self.task)

    def test_timing_handling(self):
        """Test enabling/disabling the timing.

        """
        assert 'elapsed_time' not in self.task.database_entries

        self.task.timing = True

        assert 'elapsed_time' in self.task.database_entries

        self.task.timing = False

        assert 'elapsed_time' not in self.task.database_entries

    def test_check_linspace_interface1(self, linspace_interface):
        """Test that everything is ok when all formulas are true.

        """
        self.task.interface = linspace_interface

        test, traceback = self.task.check()
        assert test
        assert not traceback
        assert self.task.get_from_database('Test_point_number') == 11

    def test_check_linspace_interface2(self, linspace_interface):
        """Test handling a wrong start.

        """
        linspace_interface.start = '1.0*'
        self.task.interface = linspace_interface

        test, traceback = self.task.check(test_instr=True)
        assert not test
        assert len(traceback) == 1
        assert 'root/Test-start' in traceback

    def test_check_linspace_interface3(self, linspace_interface):
        """Test handling a wrong stop.

        """
        linspace_interface.stop = '2.0*'
        self.task.interface = linspace_interface

        test, traceback = self.task.check(test_instr=True)
        assert not test
        assert len(traceback) == 1
        assert 'root/Test-stop' in traceback

    def test_check_linspace_interface4(self, linspace_interface):
        """Test handling a wrong step.

        """
        linspace_interface.step = '0.1*'
        self.task.interface = linspace_interface

        test, traceback = self.task.check(test_instr=True)
        assert not test
        assert len(traceback) == 1
        assert 'root/Test-step' in traceback

    def test_check_linspace_interface5(self, linspace_interface):
        """Test handling a wrong number of point.

        """
        linspace_interface.step = '0.0'
        self.task.interface = linspace_interface

        test, traceback = self.task.check(test_instr=True)
        assert not test
        assert len(traceback) == 1
        assert 'root/Test-points' in traceback

    def test_check_linspace_interface6(self, monkeypatch, linspace_interface):
        """Test handling an issue in linspace.

        """
        self.task.interface = linspace_interface
        import ecpy.tasks.tasks.logic.loop_linspace_interface as li
        monkeypatch(li, 'linspace', lambda x: x)

        test, traceback = self.task.check(test_instr=True)
        assert not test
        assert len(traceback) == 1
        assert 'root/Test-points' in traceback

    def test_check_iterable_interface1(self, iterable_interface):
        """Test that everything is ok when all formulas are true.

        """
        self.task.interface = iterable_interface

        test, traceback = self.task.check()
        assert test
        assert not traceback
        assert self.task.get_from_database('Test_point_number') == 11

        iterable_interface.iterable = 'dict(a=1)'
        test, traceback = self.task.check()
        assert test
        assert not traceback
        assert self.task.get_from_database('Test_point_number') == 1
        assert self.task.get_from_database('Test_value') == 'a'

    def test_check_iterable_interface2(self, iterable_interface):
        """Test handling a wrong iterable formula.

        """
        iterable_interface.iterable = '*range(11)'
        self.task.interface = iterable_interface

        test, traceback = self.task.check()
        assert not test
        assert len(traceback) == 1
        assert 'root/Test' in traceback

    def test_check_iterable_interface3(self, iterable_interface):
        """Test handling a wrong iterable type.

        """
        iterable_interface.iterable = '1.0'
        self.task.interface = iterable_interface

        test, traceback = self.task.check()
        assert not test
        assert len(traceback) == 1
        assert 'root/Test' in traceback

    def test_check_execution_order(self, iterable_interface):
        """Test that the interface checks are run before the children checks.

        """
        iterable_interface.iterable = '[(1, 0)]'
        self.task.interface = iterable_interface

        subiter = IterableLoopInterface(iterable='{Test_value}')
        self.task.children = [LoopTask(interface=subiter)]

        test, traceback = self.task.check()
        assert test

    def test_perform1(self, iterable_interface):
        """Test performing a simple loop no timing. Iterable interface.

        """
        self.task.interface = iterable_interface

        self.root.database.prepare_for_running()

        self.task.perform()
        assert self.root.get_from_database('Test_value') == 10

    def test_perform2(self, linspace_interface):
        """Test performing a simple loop no timing. Linspace interface.

        """
        self.task.interface = linspace_interface

        self.root.database.prepare_for_running()

        self.task.perform()
        assert self.root.get_from_database('Test_value') == 2.0

    def test_perform3(self, iterable_interface):
        """Test performing a simple loop no timing. Break.

        """
        self.task.interface = iterable_interface
        self.task.add_child_task(0, BreakTask(name='break',
                                              condition='{Test_value} == 5')
                                 )

        self.root.database.prepare_for_running()

        self.task.perform()
        assert self.root.get_from_database('Test_value') == 5

    def test_perform4(self, iterable_interface):
        """Test performing a simple loop no timing. Continue

        """
        self.task.interface = iterable_interface
        for i, t in enumerate([ContinueTask(name='break', condition='True'),
                               CheckTask(name='check')]):
            self.task.add_child_task(i, t)

        self.root.database.prepare_for_running()

        self.task.perform()
        assert not self.task.children[1].perform_called

    def test_perform_task1(self, iterable_interface):
        """Test performing a loop with an embedded task no timing.

        """
        self.task.interface = iterable_interface
        self.task.task = CheckTask(name='check')

        self.root.database.prepare_for_running()

        self.task.perform()
        assert self.root.get_from_database('Test_index') == 11
        assert self.task.task.perform_called
        assert self.task.task.perform_value == 10

    def test_perform_task2(self):
        """Test performing a loop with an embedded task no timing. Break.

        """
        interface = IterableLoopInterface()
        interface.iterable = 'range(11)'
        self.task.interface = interface
        self.task.task = CheckTask(name='check')
        self.task.add_child_task(0, BreakTask(name='Break',
                                              condition='{Test_index} == 6')
                                 )

        self.root.database.prepare_for_running()

        self.task.perform()
        assert self.root.get_from_database('Test_index') == 6
        assert self.task.task.perform_called
        assert self.task.task.perform_value == 5

    def test_perform_task3(self, iterable_interface):
        """Test performing a loop with an embedded task no timing. Continue.

        """
        self.task.interface = iterable_interface
        self.task.task = CheckTask(name='check')
        self.task.add_child_task(0, ContinueTask(name='Continue',
                                                 condition='True')
                                 )
        self.task.children.append(CheckTask(name='check'))

        self.root.database.prepare_for_running()

        self.task.perform()
        assert self.root.get_from_database('Test_index') == 11
        assert self.task.task.perform_called
        assert self.task.task.perform_value == 10
        assert not self.task.children[1].perform_called

    def test_perform_timing1(self, iterable_interface):
        """Test performing a simple loop timing.

        """
        self.task.interface = iterable_interface
        self.task.timing = True

        self.root.database.prepare_for_running()

        self.task.perform()
        assert self.root.get_from_database('Test_value') == 10
        assert self.root.get_from_database('Test_elapsed_time') != 1.0

    def test_perform_timing2(self, iterable_interface):
        """Test performing a simple loop timing. Break.

        """
        self.task.interface = iterable_interface
        self.task.timing = True
        self.task.add_child_task(0, BreakTask(name='break',
                                              condition='{Test_value} == 0')
                                 )

        self.root.database.prepare_for_running()

        self.task.perform()
        assert self.root.get_from_database('Test_value') == 0
        assert self.root.get_from_database('Test_elapsed_time') != 1.0

    def test_perform_timing3(self, iterable_interface):
        """Test performing a simple loop timing. Continue.

        """
        self.task.interface = iterable_interface
        self.task.timing = True
        self.task.add_child_task(0, ContinueTask(name='Continue',
                                                 condition='True')
                                 )
        self.task.add_child_task(1, CheckTask(name='check'))

        self.root.database.prepare_for_running()

        self.task.perform()
        assert not self.task.children[1].perform_called
        assert self.root.get_from_database('Test_elapsed_time') != 1.0

    def test_perform_timing_task1(self, iterable_interface):
        """Test performing a loop with an embedded task no timing.

        """
        self.task.interface = iterable_interface
        self.task.timing = True
        self.task.task = CheckTask(name='check')

        self.root.database.prepare_for_running()

        self.task.perform()
        assert self.root.get_from_database('Test_index') == 11
        assert self.task.task.perform_called
        assert self.task.task.perform_value == 10
        assert self.root.get_from_database('Test_elapsed_time') != 1.0

    def test_perform_timing_task2(self, iterable_interface):
        """Test performing a loop with an embedded task no timing. Break.

        """
        self.task.interface = iterable_interface
        self.task.timing = True
        self.task.task = CheckTask(name='check')
        self.task.add_child_task(BreakTask(name='break',
                                           condition='{Test_index} == 1')
                                 )

        self.root.database.prepare_for_running()

        self.task.perform()
        assert self.root.get_from_database('Test_index') == 1
        assert self.task.task.perform_called
        assert self.task.task.perform_value == 0
        assert self.root.get_from_database('Test_elapsed_time') != 1.0

    def test_perform_timing_task3(self, iterable_interface):
        """Test performing a loop with an embedded task no timing. Continue.

        """
        self.task.interface = iterable_interface
        self.task.timing = True
        self.task.task = CheckTask(name='check')
        self.task.add_child_task(0, ContinueTask(name='break',
                                                 condition='True')
                                 )
        self.task.add_child_task(1, CheckTask(name='check'))

        self.root.database.prepare_for_running()

        self.task.perform()
        assert self.root.get_from_database('Test_index') == 11
        assert self.task.task.perform_called
        assert self.task.task.perform_value == 10
        assert not self.task.children[1].perform_called
        assert self.root.get_from_database('Test_elapsed_time') != 1.0
