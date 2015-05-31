# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Handler for the commands used to save tasks.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from ..templates import save_template

import enaml
with enaml.imports():
    from ..widgets.save import (TemplateSaverDialog, ScintillaDialog)


def save_task(event):
    """ Save a task in an .ini file.

    Parameters
    ----------
    task : BaseTask
        Task to save.

    mode : {'config', 'template'}
        Should the task be returned as a dict (ConfigObj) or saved as a,
        template.

    widget : optional
        Optional widget to use as a parent for the dialog when savind as
        template.

    Returns:
    -------
    config or None:
        A dict is returned if the mode is 'config'.

    """
    full_path = u''
    mode = event.parameters['mode']
    if mode == 'template':
        manager = event.workbench.get_plugin('ecpy.tasks.manager')
        saver = TemplateSaverDialog(event.parameters.get('widget'),
                                    manager=manager)

        if saver.exec_():
            full_path = saver.get_path()
        else:
            return

    task = event.parameters['task']
    task.update_preferences_from_members()
    preferences = task.task_preferences

    if mode == 'config':
        return preferences

    else:
        doc = saver.template_doc

        save_template(full_path, preferences.dict(), doc)

        if saver.show_result:
            with open(full_path) as f:
                t = '\n'.join(f.readlines())
                ScintillaDialog(event.parameters.get('widget'),
                                text=t).exec_()
