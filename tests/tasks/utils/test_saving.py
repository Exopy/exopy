# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test saving utility functions.

"""
import os

import pytest
from configobj import ConfigObj
from enaml.widgets.api import Dialog

from exopy.tasks.api import RootTask, ComplexTask

from exopy.testing.util import handle_dialog, get_window, wait_for_destruction


CMD = 'exopy.tasks.save'


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


def test_saving_as_template(exopy_qtbot, tmpdir, task_workbench, task,
                            monkeypatch):
    """Test saving a task as a template.

    """
    from exopy.tasks.utils import saving

    monkeypatch.setattr(saving.TemplateViewer, 'exec_',
                        saving.TemplateViewer.show)

    plugin = task_workbench.get_plugin('exopy.tasks')
    plugin.templates = {'test': ''}

    def answer_dialog(bot, dialog):
        model = dialog._model
        model.folder = str(tmpdir)
        model.filename = 'test'
        model.doc = 'This is a test'
        dialog.show_result = True

        assert model.accept_template_info(dialog)

    core = task_workbench.get_plugin('enaml.workbench.core')
    with handle_dialog(exopy_qtbot, 'accept', answer_dialog):
        core.invoke_command(CMD, dict(task=task, mode='template'))

    w = get_window(exopy_qtbot, Dialog)
    w.accept()
    wait_for_destruction(exopy_qtbot, w)

    path = str(tmpdir.join('test.task.ini'))
    assert os.path.isfile(path)
    config = ConfigObj(path)
    assert config.initial_comment == ['# This is a test']


def test_saving_as_template_fail(exopy_qtbot, tmpdir, task_workbench, task,
                                 monkeypatch):
    """Test saving a task as a template : fail to save.

    """
    from exopy.tasks.utils import saving

    def false_save(path, data, doc):
        raise OSError()

    def false_critical(*args, **kwargs):
        raise RuntimeError()

    monkeypatch.setattr(saving, 'save_template', false_save)

    # We cannot easily catch a second dialog after dealing with the first
    # so we bypass it
    monkeypatch.setattr(saving, 'critical', false_critical)

    plugin = task_workbench.get_plugin('exopy.tasks')
    plugin.templates = {'test': ''}

    def answer_dialog(bot, dialog):
        model = dialog._model
        model.folder = str(tmpdir)
        model.filename = 'test'
        model.doc = 'This is a test'
        assert model.accept_template_info(dialog)

    core = task_workbench.get_plugin('enaml.workbench.core')

    with pytest.raises(RuntimeError):
        with handle_dialog(exopy_qtbot, 'accept', answer_dialog):
            core.invoke_command(CMD, dict(task=task, mode='template'))

    path = str(tmpdir.join('test.template.ini'))
    assert not os.path.isfile(path)


def test_saving_as_template_cancelled(exopy_qtbot, task_workbench, task):
    """Test saving a task as a template : fail to save.

    """
    core = task_workbench.get_plugin('enaml.workbench.core')

    with handle_dialog(exopy_qtbot, 'reject'):
        val = core.invoke_command(CMD, dict(task=task, mode='template'))

    assert val is None
