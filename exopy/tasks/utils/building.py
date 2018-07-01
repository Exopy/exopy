# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""This module implements command handler related to building tasks.

"""
import enaml

from ..tasks.base_tasks import RootTask
from .templates import load_template

with enaml.imports():
    from ..widgets.building import (BuilderView, TemplateSelector)


def create_task(event):
    """Open a dialog to include a task in a task hierarchy.

    This function is meant to be used as a Command handler. Parameters are
    passed through the parameters attributes of the event object.

    Parameters
    ----------
    parent_ui : optional
        Optional parent widget for the dialog.

    future_parent : BaseTask
        Future parent of the task

    Returns:
    -------
    task : BaseTask
        Task selected by the user to be added to a hierarchy.

    """
    manager = event.workbench.get_plugin('exopy.tasks')
    dialog = BuilderView(manager=manager,
                         parent=event.parameters.get('parent_ui'),
                         future_parent=event.parameters.get('future_parent'))
    result = dialog.exec_()
    if result:
        return dialog.config.build_task()
    else:
        return None


def build_task_from_config(config, build_dep, as_root=False):
    """Rebuild a task hierarchy from a dictionary.

    Parameters
    ----------
    config : dict
        Dictionary representing the task hierarchy.

    build_dep : Workbench or dict
        Source of the build dependencies of the hierarchy. This can either
        be the application workbench or a dict of dependencies.

    as_root : bool, optional
        Allow to force building a ComplexTask as a RootTask

    Returns
    -------
    task : BaseTask
        Newly built task.

    Raises
    ------
    RuntimeError :
        Raised if a dependency cannot be collected.

    """
    if not isinstance(build_dep, dict):
        core = build_dep.get_plugin('enaml.workbench.core')
        cmd = 'exopy.app.dependencies.analyse'
        cont = core.invoke_command(cmd, {'obj': config})
        if cont.errors:
            raise RuntimeError('Failed to analyse dependencies :\n%s' %
                               cont.errors)

        cmd = 'exopy.app.dependencies.collect'
        cont = core.invoke_command(cmd, {'kind': 'build',
                                         'dependencies': cont.dependencies})
        if cont.errors:
            raise RuntimeError('Failed to collect dependencies :\n%s' %
                               cont.errors)
        build_dep = cont.dependencies

    cls = config.pop('task_id')

    if as_root:
        return RootTask.build_from_config(config, build_dep)
    else:
        task_class = build_dep['exopy.task'][cls]
        return task_class.build_from_config(config, build_dep)


def build_root(event):
    """Create a new RootTask.

    This function is meant to be used as a Command handler. Parameters are
    passed through the parameters attributes of the event object.

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
        config = event.parameters['config']

    elif mode == 'from template':
        manager = event.workbench.get_plugin('exopy.tasks')
        view = TemplateSelector(event.parameters.get('widget'),
                                manager=manager)
        result = view.exec_()
        if result:
            path = view.path
        config, _ = load_template(path)

    else:
        msg = 'Invalid mode (%s) for build_root. Valid ones are : %s'
        raise ValueError(msg % (mode, ('from config', 'from template')))

    if config:
        build_dep = event.parameters.get('build_dep', event.workbench)
        return build_task_from_config(config, build_dep, True)

    else:
        raise RuntimeError('No config for building')
