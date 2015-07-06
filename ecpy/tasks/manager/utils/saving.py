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

from traceback import format_exc

from enaml.stdlib.message_box import critical

from .templates import save_template

import enaml
with enaml.imports():
    from ..widgets.saving import (TemplateSaverDialog, TemplateViewer)


def save_task(event):
    """Save a task in memory or in an .ini file.

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
    mode = event.parameters['mode']
    if mode == 'template':
        manager = event.workbench.get_plugin('ecpy.tasks')
        saver = TemplateSaverDialog(event.parameters.get('widget'),
                                    manager=manager)

        if not saver.exec_():
            return

    task = event.parameters['task']
    task.update_preferences_from_members()
    preferences = task.preferences

    if mode == 'config':
        return preferences

    else:
        path, doc = saver.get_infos()
        try:
            save_template(path, preferences, doc)
        except OSError:
            critical(event.parameters.get('widget'),
                     title='Failed to save',
                     text='Saving failed:\n' + format_exc())

        if saver.show_result:
            with open(path) as f:
                t = '\n'.join(f.readlines())
                TemplateViewer(event.parameters.get('widget'),
                               text=t).exec_()
