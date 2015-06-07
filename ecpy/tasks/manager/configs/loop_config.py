# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Configurer dedicated to the LoopTask allowing to specify a task to embed.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import (Typed, Unicode, Bool)

from .base_config import PyConfigTask, BaseConfigTask
from .base_config_views import BaseConfigView


class LoopConfigTask(PyConfigTask):
    """Special configurer allowing to embed a task into a LoopTask.

    """
    #: Whether or not to embed a subtask.
    use_subtask = Bool()

    #: Embedded task
    subtask = Unicode()

    #: Configurer for the subtask.
    subconfig = Typed(BaseConfigTask)

    #: View of the configurer
    subview = Typed(BaseConfigView)

    def check_parameters(self):
        """Ensure that both this config and the subconfig parameters are valid.

        """
        if self.task_name != '':
            if self.use_subtask:
                if self.subconfig is not None:
                    if self.subconfig.ready:
                        self.ready = True
                    else:
                        self.ready = False
                else:
                    self.ready = False
            else:
                self.ready = True
        else:
            self.ready = False

    def build_task(self):
        """Build the task and the potential subtask.

        """
        if self.use_subtask:
            loopable_task = self.subconfig.build_task()
            return self.task_class(task_name=self.task_name,
                                   task=loopable_task)
        else:
            return self.task_class(task_name=self.task_name)

    def _post_setattr_subtask(self, old, new):
        """handler getting the right config and config view for the subtask.

        """
        if new:
            conf, view = self.manager.config_request(new)
            conf.task_name = self.task_name
            view.loop = True
            conf.observe('ready', self._new_subconfig_status)

            self.subconfig = conf
            self.subview = view
        self.check_parameters()

    def _post_setattr_use_subtask(self, old, new):
        """Handler discarding the old subtask if subtask should not be added.

        """
        if not new:
            self.subtask = ''
            self.subconfig = None
            self.subview = None
        self.check_parameters()
