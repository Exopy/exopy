# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test of the base task functionality (exluding excution).

"""
import pytest
from atom.api import Value, List
from exopy.tasks.tasks.base_tasks import RootTask, SimpleTask, ComplexTask


class SignalListener(object):
    """Simple object to use to register emitted signals.

    """

    def __init__(self):
        self.counter = 0
        self.signals = []

    def listen(self, change):
        """Register the notification.

        """
        self.counter += 1
        self.signals.append(change)


def test_root_registering():
    """Check that the root task does write its default entries in the database
    when instantiated.

    """
    root = RootTask()
    assert root.get_from_database('default_path') == ''
    root.children = [SimpleTask(name='task2',
                                database_entries={'val2': 1},
                                root=root, parent=root,
                                database=root.database)]
    root.register_in_database()
    assert root.get_from_database('task2_val2') == 1


def test_database_operation():
    """Test setting, getting, deleting a value from the database.

    """
    root = RootTask()
    root.write_in_database('test', 1)
    assert root.get_from_database('test') == 1
    root.remove_from_database('test')
    with pytest.raises(KeyError):
        root.get_from_database('test')


def test_database_update():
    """Test that replacing the database_entries members refreshes the database.

    """
    root = RootTask()
    entries = root.database_entries.copy()
    del entries['default_path']
    entries['name'] = 'Test'
    root.database_entries = entries

    assert root.get_from_database('name') == 'Test'
    with pytest.raises(KeyError):
        root.get_from_database('default_path')


def test_database_update_with_exception():
    """Test that replacing the database_entries members refreshes the database.

    """
    root = RootTask()
    task1 = ComplexTask(name='task1',
                        database_entries={'val1': 2.0})
    task2 = SimpleTask(name='task2',
                       database_entries={'val2': 1},
                       access_exs={'val2': 1})
    task3 = ComplexTask(name='task3')
    task1.add_child_task(0, task2)
    root.add_child_task(0, task1)
    root.add_child_task(1, task3)

    assert task3.get_from_database('task2_val2')

    entries = task2.database_entries.copy()
    del entries['val2']
    task2.database_entries = entries

    with pytest.raises(KeyError):
        task1.get_from_database('task2_val2')

    with pytest.raises(KeyError):
        task3.get_from_database('task2_val2')


def test_adding_child():
    """Test adding children.

    This test adding a child with and without access_exs to a task which is not
    root and then to the root. This makes sure that giving the root afterwards
    does trigger the right updates.

    """
    root = RootTask()
    listener = SignalListener()
    root.observe('children_changed', listener.listen)
    task1 = ComplexTask(name='task1',
                        database_entries={'val1': 2.0})
    task2 = SimpleTask(name='task2',
                       database_entries={'val2': 1},
                       access_exs={'val2': 2})
    task3 = ComplexTask(name='task3')
    task1.add_child_task(0, task2)
    root.add_child_task(0, task1)
    root.add_child_task(1, task3)

    assert task1.depth == 1
    assert task1.path == 'root'
    assert task1.database is root.database
    assert task1.root is root
    assert task1.parent is root

    assert task2.depth == 2
    assert task2.path == 'root/task1'
    assert task2.database is root.database
    assert task2.root is root
    assert task2.parent is task1

    assert task1.get_from_database('task1_val1') == 2.0
    assert root.get_from_database('task1_val1') == 2.0
    assert task3.get_from_database('task2_val2') == 1

    assert listener.counter == 2
    assert all([bool(c.added) for c in listener.signals])


def test_moving_child():
    """Test moving a child.

    """
    root = RootTask()
    task1 = ComplexTask(name='task1',
                        database_entries={'val1': 2.0})
    task2 = SimpleTask(name='task2',
                       database_entries={'val2': 1},
                       access_exs={'val2': 2})
    task3 = ComplexTask(name='task3')
    task4 = ComplexTask(name='task4')

    task1.add_child_task(0, task2)
    task1.add_child_task(1, task4)
    root.add_child_task(0, task1)
    root.add_child_task(1, task3)

    listener = SignalListener()
    task1.observe('children_changed', listener.listen)

    assert task1.preferences['children_0']['name'] == 'task2'
    assert task1.preferences['children_1']['name'] == 'task4'

    task1.move_child_task(0, 1)

    assert listener.counter == 1
    assert listener.signals[0].moved

    assert task1.preferences['children_0']['name'] == 'task4'
    assert task1.preferences['children_1']['name'] == 'task2'
    assert task3.get_from_database('task2_val2') == 1


def test_deleting_child():
    """Test deleting a child.

    """
    root = RootTask()
    task1 = ComplexTask(name='task1',
                        database_entries={'val1': 2.0})
    task2 = SimpleTask(name='task2',
                       database_entries={'val2': 1},
                       access_exs={'val2': 2})
    task3 = ComplexTask(name='task3')
    task4 = ComplexTask(name='task4')

    task1.add_child_task(0, task2)
    task1.add_child_task(1, task4)
    root.add_child_task(0, task1)
    root.add_child_task(1, task3)

    listener = SignalListener()
    task1.observe('children_changed', listener.listen)

    task1.remove_child_task(0)

    assert task2.parent is None
    assert task2.root is None
    assert task2.database is None
    assert listener.counter == 1
    assert listener.signals[0].removed

    assert task1.preferences['children_0']['name'] == 'task4'
    assert 'task2_val2' not in task3.list_accessible_database_entries()

    root.remove_child_task(0)

    assert task1.parent is None
    assert task1.root is None
    assert task1.database is None
    assert task4.root is None
    assert task4.database is None
    assert len(root.children) == 1
    with pytest.raises(KeyError):
        root.get_from_database('task1_val1')


def test_moving_through_remove_add_child():
    """Test moving a child between different tasks through remove/add.

    """
    root = RootTask()
    task1 = ComplexTask(name='task1',
                        database_entries={'val1': 2.0})
    task2 = ComplexTask(name='task2',
                        database_entries={'val2': 2.0})
    task3 = SimpleTask(name='task3',
                       database_entries={'val3': 1},
                       access_exs={'val3': 2})

    task2.add_child_task(0, task3)
    task1.add_child_task(1, task2)
    root.add_child_task(0, task1)

    task1.remove_child_task(0)

    assert task2.parent is None
    assert task2.root is None
    assert task2.database is None
    assert task3.parent is not None
    assert task3.root is None
    assert task3.database is None

    root.add_child_task(0, task2)

    assert len(root.children) == 2


def test_task_renaming():
    """Test renaming simple and complex task.

    """
    root = RootTask()
    task1 = ComplexTask(name='task1',
                        database_entries={'val1': 2.0})
    task2 = ComplexTask(name='task2')
    task3 = SimpleTask(name='task3',
                       database_entries={'val2': 1},
                       access_exs={'val2': 2})

    task2.add_child_task(0, task3)
    task1.add_child_task(0, task2)
    root.add_child_task(0, task1)

    task3.name = 'worker3'
    with pytest.raises(KeyError):
        root.get_from_database('task3_val2')
    assert root.get_from_database('worker3_val2') == 1

    task1.name = 'worker1'
    with pytest.raises(KeyError):
        root.get_from_database('task1_val1')
    assert root.get_from_database('worker1_val1') == 2.0
    assert root.get_from_database('worker3_val2') == 1


def test_update_preferences_from_members():
    """Test updating the preferences.

    Only operation on the children cause re-registering to ensure the children
    ordering.

    """
    root = RootTask()
    task1 = SimpleTask(name='task1')

    root.add_child_task(0, task1)

    assert root.preferences['children_0']['name'] == 'task1'

    task1.name = 'worker1'
    assert root.preferences['children_0']['name'] == 'task1'

    root.update_preferences_from_members()
    assert root.preferences['children_0']['name'] == 'worker1'


def test_traverse():
    """Test traversing a task hierarchy to collect infos.

    """
    root = RootTask()
    task1 = ComplexTask(name='task1',
                        database_entries={'val1': 2.0})
    task2 = SimpleTask(name='task2',
                       database_entries={'val2': 1},
                       access_exs={'val2': 2})
    task3 = ComplexTask(name='task3')
    task1.add_child_task(0, task2)
    root.add_child_task(0, task1)
    root.add_child_task(1, task3)

    flat = list(root.traverse())
    assert flat == [root, task1, task2, task3]

    flat = list(root.traverse(0))
    assert flat == [root, task1, task3]


def test_access_exceptions():
    """Test adding, modifying and removing an access exception after creation.

    """
    root = RootTask()
    listener = SignalListener()
    root.observe('children_changed', listener.listen)
    task1 = ComplexTask(name='task1',
                        database_entries={'val1': 2.0})
    task2 = ComplexTask(name='task2')
    task3 = SimpleTask(name='task3',
                       database_entries={'val2': 1, 'val3': 2},
                       )

    task2.add_child_task(0, task3)
    task1.add_child_task(0, task2)
    root.add_child_task(0, task1)

    with pytest.raises(KeyError):
        task2.get_from_database('task3_val2')

    task3.add_access_exception('val2', 1)
    task3.add_access_exception('val3', 1)

    assert task2.get_from_database('task3_val2') == 1
    assert task2.get_from_database('task3_val2') == 1
    with pytest.raises(KeyError):
        task1.get_from_database('task3_val2')

    task3.modify_access_exception('val2', 2)
    task3.modify_access_exception('val3', -1)
    assert task1.get_from_database('task3_val2') == 1
    with pytest.raises(KeyError):
        task2.get_from_database('task3_val3')

    task3.remove_access_exception('val2')
    with pytest.raises(KeyError):
        task2.get_from_database('task3_val2')


def test_build_simple_from_config():
    """Test building a simple task from config.

    """
    task = SimpleTask.build_from_config({'name': 'test'}, {})
    assert task.name == 'test'


def test_build_complex_from_config():
    """Test building a complex task from config.

    """
    config = {'name': 'test',
              'children_0': {'name': 'test_child',
                             'task_id': 'SimpleTask'}}
    task = ComplexTask.build_from_config(config,
                                         {'exopy.task':
                                             {'SimpleTask': SimpleTask}})
    assert task.name == 'test'
    assert len(task.children) == 1
    assert task.children[0].name == 'test_child'
    assert isinstance(task.children[0], SimpleTask)


def test_build_root_from_config():
    """Test building a RootTask from config.

    """
    class DummyTask(SimpleTask):

        database_entries = {'test': 1}

    config = {'name': 'test',
              'children_0': {'name': 'test_child',
                             'task_id': 'DummyTask'}}
    task = RootTask.build_from_config(config,
                                      {'exopy.task':
                                          {'DummyTask': DummyTask}})
    assert task.name == 'Root'
    assert len(task.children) == 1
    assert task.children[0].name == 'test_child'
    assert task.children[0].root
    assert isinstance(task.children[0], DummyTask)
    assert task.get_from_database('test_child_test')


def test_gather_children():
    """Test _gather_children method in all corner cases.

    """

    class SuperComplexTask(ComplexTask):

        subtask = Value().tag(child=2)

        subtasks = List().tag(child=1)

    t = SimpleTask()
    sct = SuperComplexTask(subtask=1, subtasks=[2, 3],
                           children=[t])
    children = list(sct.gather_children())

    assert children == [2, 3, 1, t]
