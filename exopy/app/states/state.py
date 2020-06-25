# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""State plugin extension declaration.

"""
from atom.api import (List, Str)
from enaml.core.api import Declarative, d_


class State(Declarative):
    """Declarative class for defining a workbench state.

    State objects can be contributed as extensions child to the 'states'
    extension point of a state plugin.

    """
    #: The globally unique identifier for the state
    id = d_(Str())

    #: An optional description of what the state provides.
    description = d_(Str())

    #: The list of plugin members whose values should be reflected in the
    #: state object
    sync_members = d_(List(Str()))
