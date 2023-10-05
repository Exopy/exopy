# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------

from atom.api import (Unicode, ForwardTyped)
from configobj import ConfigObj

from ..utils.atom_util import HasPrefAtom


def environment_plugin():
    """Delayed to avoid circular references.

    """
    from .plugin import EnvironmentPlugin
    return EnvironmentPlugin


class Environment(HasPrefAtom):

    #: Name of the environment.
    name = Unicode().tag(pref=True)

    #: Reference to the environment plugin managing this environment.
    plugin = ForwardTyped(environment_plugin)

    def __init__(self, **kwargs):

        super(Environment, self).__init__(**kwargs)

    def save(self, path=None):
        """Save the environment as a ConfigObj object.

        Parameters
        ----------
        path : unicode
            Path of the file to which save the environment.

        """
        config = ConfigObj(indent_type='    ', encoding='utf-8')
        config.update(self.node.preferences_from_members())

