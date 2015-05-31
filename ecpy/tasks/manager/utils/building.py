# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""This module implements command handler related to building tasks.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import enaml

from ...base_tasks import RootTask
from ..templates import load_template

with enaml.imports():
    from ..widgets.building import (BuilderView, TemplateSelector)


def build_root_handler(event):
    """ Handler for the 'hqc_meas.task_manager.build_root' command.

    """
    manager = event.workbench.get_plugin('hqc_meas.task_manager')
    return build_root(manager, **event.parameters)


def create_task(event):
    """Open a dialog to include a task in a task hierarchy.

    Parameters are passed through the parameters attributes of the event
    object.

    Parameters:
    ----------
    parent_ui : optional
        Optional parent widget for the dialog.

    Returns:
    -------
    task : BaseTask
        Task selected by the user to be added to a hierarchy.

    """
    manager = event.workench.get_plugin('ecpy.tasks.manager')
    dialog = BuilderView(manager=manager,
                         parent=event.parameters.get('widget'))
    result = dialog.exec_()
    if result:
        return dialog.build_task()
    else:
        return None


def build_root(event):
    """Create a new RootTask.

    Parameters are passed through the parameters attributes of the event
    object.

    Parameters
    ----------
    mode : {'from config', 'from template'}
        Whether to use the given config, or look for one in templates or a
        file.

    config : configobj.Section
        Object holding the informations necessary to build the root task.

    widget : optional
        Optional parent widget for the dialog ('from template' mode only).

    build_dep : optional
        Optionnal dict containing the build dependencies.

    Returns:
    -------
    task : RootTask

    """
    mode = event.parameters['mode']
    if mode == 'from config':
        pass

    elif mode == 'from template':
        manager = event.workbench.get_plugin('ecpy.tasks.manager')
        view = TemplateSelector(event.parameters.get('widget'),
                                manager=manager)
        result = view.exec_()
        if result:
            path = view.path
        config, _ = load_template(path)

    if config:
        build_dep = event.parameters.get('build_dep')
        if build_dep is None:
            core = event.workbench.get_plugin('enaml.workbench.core')
            cmd = 'ecpy.app.dependencies.collect_from_config'
            build_dep = core.invoke_command(cmd, {'config': config})
        if isinstance(build_dep, Exception):
            return None

        config.pop('task_class')
        return RootTask.build_from_config(config, build_dep)