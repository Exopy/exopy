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
import enaml
from multiprocessing import Event

from ecpy.tasks.base_tasks import RootTask
from ecpy.tasks.tasks.logic.loop_task import LoopTask
from ecpy.tasks.tasks.logic.loop_iterable_interface\
    import IterableLoopInterface
from ecpy.tasks.tasks.logic.loop_linspace_interface\
    import LinspaceLoopInterface
from ecpy.tasks.tasks.logic.loop_exceptions_tasks\
    import BreakTask, ContinueTask

with enaml.imports():
    from ecpy.tasks.tasks.logic.views.loop_view import LoopView
    from ecpy.tasks.base_views import RootTaskView

from ...execution_testing import CheckTask
from ....util import show_and_close_widget


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

    def test_subtask_handling(self):
        """Test adding, changing, removing the subtask.

        """
        subtask1 = CheckTask(name='check', database_entries={'val': 1})
        self.task.task = subtask1

        assert subtask1.root is self.root
        assert subtask1.database is self.root.database
        assert subtask1.parent is self.task
        assert subtask1.path and subtask1.depth
        assert 'value' not in self.task.database_entries
        assert subtask1.get_from_database('check_val')
        assert self.task.preferences['task']['name'] == 'check'

        subtask2 = CheckTask(name='rep', database_entries={'new': 1})
        self.task.task = subtask2

        assert not subtask1.root
        assert not subtask1.parent
        with pytest.raises(KeyError):
            assert subtask1.get_from_database('check_val')

        assert subtask2.root is self.root
        assert subtask2.database is self.root.database
        assert subtask2.parent is self.task
        assert subtask2.path and subtask1.depth
        assert 'value' not in self.task.database_entries
        assert subtask2.get_from_database('rep_new')
        assert self.task.preferences['task']['name'] == 'rep'

        self.task.task = None

        assert not subtask2.root
        assert not subtask2.parent
        with pytest.raises(KeyError):
            assert subtask2.get_from_database('rep_new')
        assert 'value' in self.task.database_entries

    def test_traverse(self, linspace_interface):
        """Test traversing a with interfaces ComplexTask.

        """
        self.task.interface = linspace_interface
        self.task.add_child_task(0, CheckTask(name='check'))
        assert len(list(self.task.traverse())) == 3

    def test_saving_building_from_config(self, iterable_interface):
        """Done here as the LoopTask is a viable case of a member tagged with
        child.

        """
        subtask1 = CheckTask(name='check', database_entries={'val': 1})
        self.task.task = subtask1

        self.root.update_preferences_from_members()

        deps = {'ecpy.task': {'ecpy.RootTask': RootTask,
                              'ecpy.LoopTask': LoopTask,
                              'tests.CheckTask': CheckTask}
                }
        new = RootTask.build_from_config(self.root.preferences, deps)

        assert new.children[0].task.name == 'check'

        self.task.interface = iterable_interface
        self.root.update_preferences_from_members()
        prefs = self.root.preferences
        del prefs['children_0']['task']
        deps = {'ecpy.task': {'ecpy.RootTask': RootTask,
                              'ecpy.LoopTask': LoopTask,
                              'tests.CheckTask': CheckTask},
                'ecpy.tasks.interface':
                    {('IterableLoopInterface', ('ecpy.LoopTask',)):
                        IterableLoopInterface}
                }
        new = RootTask.build_from_config(prefs, deps)

        assert not new.children[0].task

    def test_timing_handling(self):
        """Test enabling/disabling the timing.

        """
        assert 'elapsed_time' not in self.task.database_entries

        self.task.timing = True

        assert 'elapsed_time' in self.task.database_entries

        self.task.timing = False

        assert 'elapsed_time' not in self.task.database_entries

    def test_check_missing(self):
        """Test handling a missing interface (check overridden so necessary).

        """
        res, tb = self.task.check()

        assert not res
        assert len(tb) == 1
        assert 'root/Test-interface' in tb

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
        monkeypatch.setattr(li, 'linspace', lambda x: x)

        test, traceback = self.task.check(test_instr=True)
        assert not test
        assert len(traceback) == 1
        assert 'root/Test-linspace' in traceback

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
        assert 'root/Test-iterable' in traceback

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
        self.task.add_child_task(0, LoopTask(interface=subiter))

        test, traceback = self.task.check()
        print(traceback)
        assert test

    def test_perform1(self, iterable_interface):
        """Test performing a simple loop no timing. Iterable interface.

        """
        self.task.interface = iterable_interface
        self.root.database.prepare_to_run()
        self.root.check()

        self.task.perform()
        assert self.root.get_from_database('Test_value') == 10

    def test_perform2(self, linspace_interface):
        """Test performing a simple loop no timing. Linspace interface.

        """
        self.task.interface = linspace_interface
        self.root.database.prepare_to_run()
        self.root.check()

        self.task.perform()
        assert self.root.get_from_database('Test_value') == 2.0

    def test_perform3(self, iterable_interface):
        """Test performing a simple loop no timing. Break.

        """
        self.task.interface = iterable_interface
        self.task.add_child_task(0, BreakTask(name='break',
                                              condition='{Test_value} == 5')
                                 )
        self.root.database.prepare_to_run()
        self.root.check()

        self.task.perform()
        assert self.root.get_from_database('Test_value') == 5

    def test_perform4(self, iterable_interface):
        """Test performing a simple loop no timing. Continue

        """
        self.task.interface = iterable_interface
        for i, t in enumerate([ContinueTask(name='break', condition='True'),
                               CheckTask(name='check')]):
            self.task.add_child_task(i, t)

        self.root.database.prepare_to_run()
        self.root.check()

        self.task.perform()
        assert not self.task.children[1].perform_called

    def test_perform_task1(self, iterable_interface):
        """Test performing a loop with an embedded task no timing.

        """
        self.task.interface = iterable_interface
        self.task.task = CheckTask(name='check')
        self.root.database.prepare_to_run()
        self.root.check()

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
        self.root.database.prepare_to_run()
        self.root.check()

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
        self.root.database.prepare_to_run()
        self.root.check()

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
        self.root.database.prepare_to_run()
        self.root.check()

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

        self.root.database.prepare_to_run()
        self.root.check()

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
        self.root.database.prepare_to_run()
        self.root.check()

        self.task.perform()
        assert not self.task.children[1].perform_called
        assert self.root.get_from_database('Test_elapsed_time') != 1.0

    def test_perform_timing_task1(self, iterable_interface):
        """Test performing a loop with an embedded task no timing.

        """
        self.task.interface = iterable_interface
        self.task.timing = True
        self.task.task = CheckTask(name='check')

        self.root.database.prepare_to_run()
        self.root.check()

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
        self.task.add_child_task(0, BreakTask(name='break',
                                              condition='{Test_index} == 1')
                                 )

        self.root.database.prepare_to_run()
        self.root.check()

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

        self.root.database.prepare_to_run()
        self.root.check()

        self.task.perform()
        assert self.root.get_from_database('Test_index') == 11
        assert self.task.task.perform_called
        assert self.task.task.perform_value == 10
        assert not self.task.children[1].perform_called
        assert self.root.get_from_database('Test_elapsed_time') != 1.0

    def test_performing_stop1(self, iterable_interface):
        """Test handling stop in the middle of an iteration.

        no child, no timing.

        """
        self.task.interface = iterable_interface
        stop = lambda t, v: t.root.should_stop.set()
        self.task.add_child_task(0, CheckTask(name='Stop', custom=stop,
                                              stoppable=False))
        self.root.check()

        self.task.perform()

        assert self.task.children[0].perform_called == 1

    def test_performing_stop2(self, iterable_interface):
        """Test handling stop in the middle of an iteration.

        No child, timing.

        """
        self.task.timing = True
        self.task.interface = iterable_interface
        stop = lambda t, v: t.root.should_stop.set()
        self.task.add_child_task(0, CheckTask(name='Stop', custom=stop,
                                              stoppable=False))
        self.root.check()

        self.task.perform()

        assert self.task.children[0].perform_called == 1

    def test_performing_stop3(self, iterable_interface):
        """Test handling stop in the middle of an iteration.

        Child, no timing

        """
        self.task.interface = iterable_interface
        self.task.task = CheckTask(name='check')
        stop = lambda t, v: t.root.should_stop.set()
        self.task.add_child_task(0, CheckTask(name='Stop', custom=stop,
                                              stoppable=False))
        self.root.check()

        self.task.perform()

        assert self.task.children[0].perform_called == 1

    def test_performing_stop4(self, iterable_interface):
        """Test handling stop in the middle of an iteration.

        Child, timing

        """
        self.task.timing = True
        self.task.interface = iterable_interface
        self.task.task = CheckTask(name='check')
        stop = lambda t, v: t.root.should_stop.set()
        self.task.add_child_task(0, CheckTask(name='Stop', custom=stop,
                                              stoppable=False))
        self.root.check()

        self.task.perform()

        assert self.task.children[0].perform_called == 1


from ...manager.conftest import task_workbench

@pytest.mark.ui
def test_view(windows, task_workbench):
    """Test the LoopTask view.

    """
    root = RootTaskView(core=task_workbench.get_plugin('enaml.workbench.core'))
    task = LoopTask(name='Test', interface=IterableLoopInterface())
    show_and_close_widget(LoopView(task=task, root=root))


@pytest.mark.ui
def test_view_with_subtask(windows, task_workbench):
    """Test the ConditionalTask view.

    """
    root = RootTaskView(core=task_workbench.get_plugin('enaml.workbench.core'))
    task = LoopTask(name='Test', interface=LinspaceLoopInterface(),
                    task=BreakTask(name='Aux'))
    show_and_close_widget(LoopView(task=task, root=root))
