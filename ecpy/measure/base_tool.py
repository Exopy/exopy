# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Measure tools are meant to specify actions not covered by the tasks.

The class defined here are not meant to be used directly. One should rather
subclass one of their subclasses according to the kind of tool one wants to
create.

The existing kind of tools are the following :

- pre-measure execution hook : used to perform additional operations before
  running a measure. (see `hooks` package)
- monitors : used to follow the progress of a measure. (see `monitors` package)
- post-measure execution hook : used to perform additional operations after the
  measure has been run. (see `hooks` package)

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import ForwardTyped, Unicode, Bool
from enaml.core.api import Declarative, d_, d_func

from ..utils.atom_util import HasPrefAtom


def tool_decl():
    return BaseToolDeclaration


def measure():
    from .measure import Measure
    return Measure


class BaseMeasureTool(HasPrefAtom):
    """Base tool simply definig the expected interface.

    """
    #: Reference to the measure to which that tool is linked (None if unlinked)
    measure = ForwardTyped(measure)

    #: Reference to the declaration of this tool.
    declaration = ForwardTyped(tool_decl)

    def check(self, workbench, **kwargs):
        """Ensure that the tool is properly configured and will be able to work

        Parameters
        ----------
        workbench :
            Reference to the application workbench.

        kwargs :
            Additional keywords providing infos about the context of execution.
            For example if any runtime dependencie is unavailable it will be
            listed in the missing keyword argument.

        """
        return True, {}

    def get_state(self):
        """Get the current state of the tool. Used when saving.

        """
        return self.preferences_from_members()

    def set_state(self, state):
        """Restore the state of the tool from a preferences dict.

        """
        self.update_members_from_preferences(state)

    def link_to_measure(self, measure):
        """Link this tool to a measure.

        """
        self.measure = measure

    def unlink_from_measure(self):
        """Unlink this tool from the measure to which it is linked.
        """
        del self.measure


class BaseToolDeclaration(Declarative):
    """Base class for defining a measure tool contribution.

    """
    #: Unique name used to identify the tool.
    #: The usual format is top_level_package_name.tool_name
    id = d_(Unicode())

    #: Description of the tool.
    description = d_(Unicode())

    #: Flag indicating whether the tool has an associated parametrisation
    #: widget.
    has_view = d_(Bool())

    @d_func
    def new(self, workbench, default=True):
        """Create a new instance of the tool.

        Parameters
        ----------
        workbench : Workbench
            Reference to the application workbench.

        default : bool, optional
            Flag indicating whether to use default parameters when creating the
            tool or not. Mainly used when loading a tool from a saved config.

        """
        raise NotImplementedError()

    @d_func
    def make_view(self, workbench, tool):
        """Create a widget to edit the tool parameters.

        This widget should inherit from Container.

        """
        pass
