# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Standard task configurers.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import random

from atom.api import (Atom, Bool, Unicode, Subclass, ForwardTyped)

from inspect import getdoc

from ...base_tasks import BaseTask
from ..utils.templates import load_template
from ..utils.building import build_task_from_config


# Circular import protection
def task_manager():
    from ..plugin import TaskManagerPlugin
    return TaskManagerPlugin


class BaseTaskConfig(Atom):
    """Base class for task configurer.

    """
    #: Task manager, necessary to retrieve task implementations.
    manager = ForwardTyped(task_manager)

    #: Name of the task to create.
    task_name = Unicode()

    #: Class of the task to create.
    task_class = Subclass(BaseTask)

    #: Bool indicating if the build can be done.
    ready = Bool(False)

    def check_parameters(self):
        """The only parameter required is a valid task name.

        """
        self.ready = bool(self.task_name)

    def build_task(self):
        """This method use the user parameters to build the task object

         Returns
        -------
        task : BaseTask
            Task object built using the user parameters. Ready to be
            inserted in a task hierarchy.

        """
        raise NotImplementedError()

    def _post_setattr_task_name(self, old, new):
        """Everytime the task name change check whether ornot it is valid.

        """
        self.check_parameters()

    def _default_task_name(self):
        names = self.manager.auto_task_names
        if names:
            return random.choice(names)
        else:
            return ''


class PyTaskConfig(BaseTaskConfig):
    """ Standard configurer for python tasks.

    This configurer is suitable for most python task whose initialisation
    simply requires a name.

    """
    # Docstring of the class to help pepole know what they are going to create.
    task_doc = Unicode()

    def __init__(self, **kwargs):
        super(PyTaskConfig, self).__init__(**kwargs)
        self.task_doc = getdoc(self.task_class).replace('\n', ' ')

    def build_task(self):
        return self.task_class(task_name=self.task_name)


class TemplateTaskConfig(BaseTaskConfig):
    """Configurer for template task.

    This configurer use the data stored about a task hierarchy to rebuild it
    from scratch.

    """
    #: Path to the file storing the hierarchy.
    template_path = Unicode()

    #: Description of the template.
    template_doc = Unicode()

    def __init__(self, **kwargs):
        super(TemplateTaskConfig, self).__init__(**kwargs)
        if self.template_path:
            _, doc = load_template(self.template_path)
            self.template_doc = doc

    def build_task(self):
        """Build the task stored in the selected template.

        """
        config, _ = load_template(self.template_path)
        built_task = build_task_from_config(config, self.manager)
        return built_task
