# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Base classes for all editors.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Unicode, Typed, Bool, ForwardTyped, Int
from enaml.core.api import Declarative, d_, d_func
from enaml.widgets.api import Page

from ...tasks.api import BaseTask


class BaseEditor(Page):
    """Base class for all editors.

    """
    #: Declaration defining this editor.
    declaration = ForwardTyped(lambda: Editor)

    #: Currently selected task in the tree.
    selected_task = d_(Typed(BaseTask))

    #: Should the tree be visible when this editor is selected.
    tree_visible = d_(Bool(True))

    #: Should the tree be enabled when this editor is selected.
    tree_enabled = d_(Bool(True))

    @d_func
    def react_to_selection(self, workbench):
        """Take any necessary actions when the editor is selected.

        This method is called by the framework at the appropriate time.

        Parameters
        ----------
        workbench : Workbench
            Reference to the application workbench.

        """
        pass

    @d_func
    def react_to_unselection(self, workbench):
        """Take any necessary actions when the editor is unselected.

        This method is called by the framework at the appropriate time.

        Parameters
        ----------
        workbench : Workbench
            Reference to the application workbench.

        """
        pass

    def _default_name(self):
        """Set the name of the widget otherwise the notebook does not work well

        """
        return self.declaration.id


class Editor(Declarative):
    """A declarative class for contributing a measure editor.

    Editor object can be contributed as extensions child to the 'editors'
    extension point of the 'ecpy.measure' plugin.

    """
    #: Unique name used to identify the editor. Should be user understandable.
    id = d_(Unicode())

    #: Editor description.
    description = d_(Unicode())

    #: Rank of this editor. Editors are displayed by rank and alphabetical
    #: order
    rank = d_(Int(100))

    @d_func
    def new(self, workbench, default=True):
        """Create a new instance of the editor.

        Parameters
        ----------
        workbench : Workbench
            Reference to the application workbench.

        default : bool
            Whether to use default parameters or not when creating the object.

        """
        raise NotImplementedError()

    @d_func
    def is_meant_for(self, workbench, selected_task):
        """Determine if the editor is fit to be used for the selected task.

        Parameters
        ----------
        workbench : Workbench
            Reference to the application workbench.

        selected_task : BaseTask
            Currently selected task.

        Returns
        -------
        answer : bool

        """
        raise NotImplementedError()
