# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Measurement tools are meant to specify actions not covered by the tasks.

The class defined here are not meant to be used directly. One should rather
subclass one of their subclasses according to the kind of tool one wants to
create.

The existing kind of tools are the following :

- pre-measurement execution hook : used to perform additional operations before
  running a measurement. (see `hooks` package)
- monitors : used to follow the progress of a measurement. (see `monitors`
  package)
- post-measurement execution hook : used to perform additional operations after
  the measurement has been run. (see `hooks` package)

"""
import sys

from atom.api import ForwardTyped, Unicode, Bool
from enaml.core.api import Declarative, d_, d_func

from ..utils.atom_util import HasPrefAtom


def tool_decl():
    """Forward typing for the declaration member of the BaseMeasureTool.

    """
    return BaseToolDeclaration


def measurement():
    """Delayed import to avoid circular import issues.

    """
    from .measurement import Measurement
    return Measurement


class BaseMeasureTool(HasPrefAtom):
    """Base tool simply definig the expected interface.

    """
    #: Reference to the measurement to which that tool is linked
    #: (None if unlinked)
    measurement = ForwardTyped(measurement)

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

    def link_to_measurement(self, measurement):
        """Link this tool to a measurement.

        """
        self.measurement = measurement

    def unlink_from_measurement(self):
        """Unlink this tool from the measurement to which it is linked.
        """
        del self.measurement


class BaseToolDeclaration(Declarative):
    """Base class for defining a measurement tool contribution.

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

    def _default_has_view(self):
        member = self.make_view
        func = getattr(member, 'im_func',
                       getattr(member, '__func__', None))
        return func is not BaseToolDeclaration.make_view
