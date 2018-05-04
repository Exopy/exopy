# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test of the LoopTask.

"""
from multiprocessing import Event

import pytest
import enaml
import numpy as np

from exopy.testing.tasks.util import CheckTask
from exopy.testing.util import show_and_close_widget, show_widget
from exopy.tasks.api import RootTask
from exopy.tasks.tasks.logic.loop_task import LoopTask
from exopy.tasks.tasks.logic.loop_iterable_interface\
    import IterableLoopInterface
from exopy.tasks.tasks.logic.loop_linspace_interface\
    import LinspaceLoopInterface
from exopy.tasks.tasks.logic.loop_exceptions_tasks\
    import BreakTask, ContinueTask

with enaml.imports():
    from exopy.tasks.tasks.logic.views.loop_view import LoopView
    from exopy.tasks.tasks.base_views import RootTaskView


pytest_plugins = str('exopy.testing.tasks.fixtures'),


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


def false_perform_loop(self, iterable):
    """Used to patch LoopTask for testing.

    """
    self.database_entries = {'iterable': iterable}


def test_linspace_handling_of_step_sign(monkeypatch, linspace_interface):
    """Test that no matter the sign of step we generate the proper array.

    """
    monkeypatch.setattr(LoopTask, 'perform_loop', false_perform_loop)
    root = RootTask(should_stop=Event(), should_pause=Event())
    lt = LoopTask(name='Test')
    root.add_child_task(0, lt)

    lt.interface = linspace_interface
    linspace_interface.step = '-0.1'
    linspace_interface.perform()
    expected = np.array([1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0]
                        )
    np.testing.assert_array_equal(lt.database_entries['iterable'], expected)

    linspace_interface.start = '3.0'
    linspace_interface.perform()
    expected = np.array([3.0, 2.9, 2.8, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0]
                        )
    np.testing.assert_array_equal(lt.database_entries['iterable'],
                                  expected)


def test_linspace_handling_of_rounding(monkeypatch, linspace_interface):
    """Test that we properly round the values.

    """
    monkeypatch.setattr(LoopTask, 'perform_loop', false_perform_loop)
    root = RootTask(should_stop=Event(), should_pause=Event())
    lt = LoopTask(name='Test')
    root.add_child_task(0, lt)

    # Step use more digit
    lt.interface = linspace_interface
    linspace_interface.start = '0.1'
    linspace_interface.stop = '0.11'
    linspace_interface.step = '0.001'
    linspace_interface.perform()
    expected = np.array([0.1, 0.101, 0.102, 0.103, 0.104, 0.105, 0.106,
                         0.107, 0.108, 0.109, 0.11])
    # Check that this does indeed cause a rounding issue
    with pytest.raises(AssertionError):
        np.testing.assert_array_equal(np.linspace(0.1, 0.11, 11), expected)
    np.testing.assert_array_equal(lt.database_entries['iterable'], expected)

    # Start use more digit
    lt.interface = linspace_interface
    linspace_interface.start = '1.01'
    linspace_interface.stop = '2.01'
    linspace_interface.step = '0.1'
    linspace_interface.perform()
    expected = np.array([1.01, 1.11, 1.21, 1.31, 1.41, 1.51, 1.61, 1.71, 1.81,
                         1.91, 2.01])
    np.testing.assert_array_equal(lt.database_entries['iterable'], expected)

    # Start use more digit and stop does not round properly
    lt.interface = linspace_interface
    linspace_interface.start = '0.501'
    linspace_interface.stop = '1'
    linspace_interface.step = '0.2'
    linspace_interface.perform()
    expected = np.array([0.501, 0.701, 0.901])
    np.testing.assert_array_equal(lt.database_entries['iterable'], expected)


def test_linspace_handling_of_non_matching_stop(monkeypatch,
                                                linspace_interface):
    """Test that we respect the step even if stop does not match.

    """
    monkeypatch.setattr(LoopTask, 'perform_loop', false_perform_loop)
    root = RootTask(should_stop=Event(), should_pause=Event())
    lt = LoopTask(name='Test')
    root.add_child_task(0, lt)

    lt.interface = linspace_interface
    linspace_interface.start = '0.1'
    linspace_interface.stop = '0.1101'
    linspace_interface.step = '0.001'
    linspace_interface.perform()
    expected = np.array([0.1, 0.101, 0.102, 0.103, 0.104, 0.105, 0.106,
                         0.107, 0.108, 0.109, 0.11])
    np.testing.assert_array_equal(lt.database_entries['iterable'], expected)


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
        assert subtask1.get_from_database('Test_val')
        assert self.task.preferences['task']['name'] == 'Test'

        subtask2 = CheckTask(name='rep', database_entries={'new': 1})
        self.task.task = subtask2

        assert not subtask1.root
        assert not subtask1.parent
        with pytest.raises(KeyError):
            subtask1.get_from_database('Test_val')

        assert subtask2.root is self.root
        assert subtask2.database is self.root.database
        assert subtask2.parent is self.task
        assert subtask2.path and subtask1.depth
        assert 'value' not in self.task.database_entries
        assert subtask2.get_from_database('Test_new')
        assert self.task.preferences['task']['name'] == 'Test'

        self.task.name += '2'
        assert subtask2.name == self.task.name

        self.task.task = None

        assert not subtask2.root
        assert not subtask2.parent
        with pytest.raises(KeyError):
            subtask2.get_from_database('Test2_new')
        assert 'value' in self.task.database_entries

        # check that we handle properly the case of no subtask
        self.task.name += '2'

    def test_renaming(self):
        """Test renaming the task.

        """
        subtask1 = CheckTask(name='check', database_entries={'val': 1})
        self.task.task = subtask1
        assert subtask1.get_from_database('Test_val') == 1

        self.task.name = 'Test2'
        assert subtask1.get_from_database('Test2_val') == 1
        assert self.task.get_from_database('Test2_point_number') == 11

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

        deps = {'exopy.task': {'exopy.RootTask': RootTask,
                               'exopy.LoopTask': LoopTask,
                               'exopy.CheckTask': CheckTask}
                }
        new = RootTask.build_from_config(self.root.preferences, deps)

        assert new.children[0].task.name == 'Test'

        self.task.interface = iterable_interface
        self.root.update_preferences_from_members()
        prefs = self.root.preferences
        assert prefs['children_0'].sections[1] == 'task'
        del prefs['children_0']['task']
        deps = {'exopy.task': {'exopy.RootTask': RootTask,
                               'exopy.LoopTask': LoopTask,
                               'exopy.CheckTask': CheckTask},
                'exopy.tasks.interface':
                    {'exopy.LoopTask:exopy.IterableLoopInterface':
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
        assert self.task.get_from_database('Test_value') == 1.0

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
        import exopy.tasks.tasks.logic.loop_linspace_interface as li
        monkeypatch.setattr(li.np, 'arange', lambda x: x)

        test, traceback = self.task.check(test_instr=True)
        assert not test
        assert len(traceback) == 1
        assert 'root/Test-arange' in traceback

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
        assert 'root/Test-iterable' in traceback

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
        self.root.prepare()

        self.task.perform()
        assert self.root.get_from_database('Test_value') == 10

    def test_perform2(self, linspace_interface):
        """Test performing a simple loop no timing. Linspace interface.

        """
        self.task.interface = linspace_interface
        self.root.prepare()

        self.task.perform()
        assert self.root.get_from_database('Test_value') == 2.0

    def test_perform3(self, iterable_interface):
        """Test performing a simple loop no timing. Break.

        """
        self.task.interface = iterable_interface
        self.task.add_child_task(0, BreakTask(name='break',
                                              condition='{Test_value} == 5')
                                 )
        self.root.prepare()

        self.task.perform()
        assert self.root.get_from_database('Test_value') == 5

    def test_perform4(self, iterable_interface):
        """Test performing a simple loop no timing. Continue

        """
        self.task.interface = iterable_interface
        for i, t in enumerate([ContinueTask(name='break', condition='True'),
                               CheckTask(name='check')]):
            self.task.add_child_task(i, t)

        self.root.prepare()

        self.task.perform()
        assert not self.task.children[1].perform_called

    def test_perform_task1(self, iterable_interface):
        """Test performing a loop with an embedded task no timing.

        """
        self.task.interface = iterable_interface
        self.task.task = CheckTask(name='check')
        self.root.prepare()

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
        self.root.prepare()

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
        self.root.prepare()

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
        self.root.prepare()

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

        self.root.prepare()

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

        self.root.prepare()

        self.task.perform()
        assert not self.task.children[1].perform_called
        assert self.root.get_from_database('Test_elapsed_time') != 1.0

    def test_perform_timing_task1(self, iterable_interface):
        """Test performing a loop with an embedded task no timing.

        """
        self.task.interface = iterable_interface
        self.task.timing = True
        self.task.task = CheckTask(name='check')

        self.root.prepare()

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

        self.root.prepare()

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

        self.root.prepare()

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
        self.task.prepare()

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
        self.task.prepare()

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
        self.task.prepare()

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
        self.task.prepare()

        self.task.perform()

        assert self.task.children[0].perform_called == 1

    def test_view(self, exopy_qtbot, task_workbench):
        """Test the LoopTask view.

        """
        core = task_workbench.get_plugin('enaml.workbench.core')
        root = RootTaskView(core=core)
        show_and_close_widget(exopy_qtbot, LoopView(task=self.task, root=root))

    def test_view_interface_not_inline(self, exopy_qtbot, task_workbench,
                                       linspace_interface):
        """Test the LoopTask view.

        """
        core = task_workbench.get_plugin('enaml.workbench.core')
        root = RootTaskView(core=core)
        self.task.interface = linspace_interface
        show_and_close_widget(exopy_qtbot, LoopView(task=self.task, root=root))

    def test_view_with_subtask(self, exopy_qtbot, task_workbench):
        """Test the LoopTask view.

        """
        core = task_workbench.get_plugin('enaml.workbench.core')
        root = RootTaskView(core=core)
        self.task.task = BreakTask(name='Aux')
        show_and_close_widget(exopy_qtbot, LoopView(task=self.task, root=root))

    def test_view_changing_interface(self, exopy_qtbot, task_workbench):
        """Test the LoopTask view.

        """
        core = task_workbench.get_plugin('enaml.workbench.core')
        root = RootTaskView(core=core)
        view = LoopView(task=self.task, root=root)
        show_widget(exopy_qtbot, view)
        selector = view.widgets()[2]
        current_interface = view.task.interface
        selector.selected = selector.items[1]

        def assert_interface_changed():
            assert view.task.interface is not current_interface
        exopy_qtbot.wait_until(assert_interface_changed)

        current_interface = view.task.interface
        selector.selected = selector.items[0]

        def assert_interface_changed():
            assert view.task.interface is not current_interface
        exopy_qtbot.wait_until(assert_interface_changed)
