# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the AddTask post hook.

"""
import pytest
from exopy.tasks.api import RootTask, SimpleTask
from enaml.workbench.api import Workbench
from exopy.testing.measurement.dummies import DummyEngine
from exopy.tasks.tasks.base_views import RootTaskView


@pytest.fixture
def addtaskhook(measurement):
    """Create an AddTaskHook.

    """
    hook = measurement.plugin.create('post-hook', 'exopy.addtask_hook')
    return hook

@pytest.fixture
def addtaskview(measurement_workbench, addtaskhook):
    """Create an AddTaskView.

    """
    # on est obligé d'aller chercher dans le vrai manifest de measurement pour
    # trouver le make_view
    meas = measurement_workbench.get_plugin('exopy.measurement')
    decl = meas.get_declarations('exopy.addtask_hook') # check how to get the declaration
    view = decl.make_view(measurement_workbench, addtaskhook)
    return view


def test_new_addtask_hook(addtaskhook):
    """Testing the creation of an AddTask post-hook

    """
    assert type(addtaskhook.root_task) == RootTask
    assert type(addtaskhook.workbench) == Workbench
    # assert hook.default_path
    # assert hook.dependencies
    # assert hook.engine


def test_get_state(addtaskhook):
    """Testing saving the hook

    """
    root = addtaskhook.root_task
    root.children = [SimpleTask(name='task',
                                database_entries={'val': 1},
                                root=root, parent=root,
                                database=root.database)]
    task_prefs = addtaskhook.get_state()
    print(task_prefs)
    # config = {'name': 'test',
    #       'children_0': {'name': 'test_child',
    #                      'task_id': 'DummyTask'}}
    assert task_prefs  # blabla selon sa structure


def test_set_state(addtaskhook):
    """Testing loading the hook from config

    """
    config = {}  # config avec 1 tache SimpleTask
    addtaskhook.set_state(config)
    root = addtaskhook.root_task
    assert len(root.children) == 1
    assert root.name == 'post_hooks'
    assert isinstance(root.children[0], SimpleTask)


def test_pause(addtaskhook):
    """Testing the engine pause

    """
    addtaskhook.engine = DummyEngine()
    addtaskhook.pause()
    assert addtaskhook.engine.should_pause == True


def test_resume(addtaskhook):
    """Testing the engine resume

    """
    addtaskhook.engine = DummyEngine()
    addtaskhook.resume()
    assert addtaskhook.engine.should_resume == True


def test_stop(addtaskhook):
    """Testing the engine stop

    """
    addtaskhook.engine = DummyEngine()
    addtaskhook.stop(force=False)
    assert addtaskhook.engine.stop_called == True


def test_force_stop(addtaskhook):
    """Testing the engine force stop

    """
    addtaskhook.engine = DummyEngine()
    addtaskhook.stop(force=True)
    assert addtaskhook.engine.stop_called == True

def test_view(addtaskview, addtaskhook):
    """Testing the view

    """
    assert addtaskview.hook
    assert addtaskview.declaration.id == 'exopy.addtask_hook'
    assert addtaskview.workbench
    assert type(addtaskview.widget()[0]) == RootTaskView
    rootview = addtaskview.widget()[0]
    assert rootview.show_path == False
    # ca devrait marcher pcq on appelle une seule fois la fixture, ensuite c'est le même objet
    assert rootview.task == addtaskhook.root_task

def test_list_runtimes():
    """Testing list_runtimes

    TODO
    """