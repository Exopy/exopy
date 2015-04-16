# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""State plugin definition.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import List, Unicode, Callable
from enaml.core.declarative import Declarative, d_


class Preferences(Declarative):
    """ Declarative class for defining a workbench preference contribution.

    Preferences object can be contributed as extensions child to the 'prefs'
    extension point of a preference plugin.

    """
    #: Name of the method of the plugin contributing this extension to call
    #: when the preference plugin need to save the preferences.
    saving_method = d_(Unicode('preferences_from_members'))

    #: Name of the method of the plugin contributing this extension to call
    #: when the preference plugin need to load preferences.
    loading_method = d_(Unicode('update_members_from_preferences'))

    #: The list of plugin members whose values should be observed and whose
    #: update should cause and automatic update of the preferences.
    auto_save = d_(List())

    #: A callable taking the plugin_id and the preference declaration as arg
    #: and returning an autonomous enaml view (Container) used to edit
    #: the preferences. It should have a model attribute. The model members
    #: must correspond to the tagged members the plugin, their values will be
    #: used to update the preferences.
    edit_view = d_(Callable())
