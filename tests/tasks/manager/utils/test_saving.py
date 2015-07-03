# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test saving utility functions.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os

import pytest
from configobj import ConfigObj

from ecpy.tasks.api import RootTask, ComplexTask

from ....util import handle_dialog, process_app_events, get_window


CMD = 'ecpy.tasks.save'


@pytest.fixture
def task():
    root = RootTask()
    root.add_child_task(0, ComplexTask(name='Dummy'))
    return root


def test_saving_as_config(task_workbench, task):
    """Test simply getting the config representation of a task.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')
    val = core.invoke_command(CMD, dict(task=task, mode='config'))

    assert val == task.preferences


def test_saving_as_template(app, tmpdir, task_workbench, task,
                            monkeypatch):
    """Test saving a task as a template.

    """
    from ecpy.tasks.manager.utils import saving

    monkeypatch.setattr(saving.TemplateViewer, 'exec_',
                        saving.TemplateViewer.show)

    plugin = task_workbench.get_plugin('ecpy.tasks')
    plugin.templates = {'test': ''}

    def answer_dialog(dialog):
        model = dialog._model
        model.folder = str(tmpdir)
        model.filename = 'test'
        model.doc = 'This is a test'
        dialog.show_result = True
        with handle_dialog('accept'):
            assert model.accept_template_info(dialog)

    core = task_workbench.get_plugin('enaml.workbench.core')
    with handle_dialog('accept', answer_dialog):
        core.invoke_command(CMD, dict(task=task, mode='template'))

    process_app_events()
    get_window().accept()
    process_app_events()

    path = str(tmpdir.join('test.template.ini'))
    assert os.path.isfile(path)
    config = ConfigObj(path)
    assert config.initial_comment == ['# This is a test']


def test_saving_as_template_fail(app, tmpdir, task_workbench, task,
                                 monkeypatch):
    """Test saving a task as a template : fail to save.

    """
    from ecpy.tasks.manager.utils import saving

    def false_save(path, data, doc):
        raise OSError()

    def false_critical(*args, **kwargs):
        raise RuntimeError()

    monkeypatch.setattr(saving, 'save_template', false_save)

    # Critical use windows dialog on windows and are then not in the windows
    # set.
    monkeypatch.setattr(saving, 'critical', false_critical)

    plugin = task_workbench.get_plugin('ecpy.tasks')
    plugin.templates = {'test': ''}

    def answer_dialog(dialog):
        model = dialog._model
        model.folder = str(tmpdir)
        model.filename = 'test'
        model.doc = 'This is a test'
        with handle_dialog('accept'):
            assert model.accept_template_info(dialog)

    core = task_workbench.get_plugin('enaml.workbench.core')

    with pytest.raises(RuntimeError):
        with handle_dialog('accept', answer_dialog):
            core.invoke_command(CMD, dict(task=task, mode='template'))

    path = str(tmpdir.join('test.template.ini'))
    assert not os.path.isfile(path)


def test_saving_as_template_cancelled(app, task_workbench, task):
    """Test saving a task as a template : fail to save.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')

    with handle_dialog('reject'):
        val = core.invoke_command(CMD, dict(task=task, mode='template'))

    assert val is None
