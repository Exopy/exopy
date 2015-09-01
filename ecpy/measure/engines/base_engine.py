# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Base classes for all engines

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Atom, Unicode, ForwardTyped, Signal, Enum
from enaml.core.api import Declarative, d_, d_func


class TaskInfos(Atom):
    """Container task containing a task to execute and additional infos.

    """
    pass


class BaseEngine(Atom):
    """Base class for all engines.

    """
    #: Declaration defining this engine.
    declaration = ForwardTyped(lambda: Engine)

    #: Current status of the engine.
    status = Enum('Stopped', 'Waiting', 'Running', 'Pausing', 'Paused',
                  'Resuming')

    #: Signal used to pass news about the measurement progress.
    progress = Signal()

    def perform(self, task_infos):
        """Execute a given task hierarchy.

        Returns
        -------
        # XXXX

        """
        raise NotImplementedError()

    def pause(self):
        """Ask the engine to pause the current task.

        This method should not wait for the task to pause to return.
        When the pause is effective the engine should signal it by updating its
        status.

        """
        raise NotImplementedError()

    def resume(self):
        """Ask the engine to resume the currently paused task.

        This method should not wait for the measure to resume.
        When the pause is over the engine should signal it by updating its
        status.

        """
        raise NotImplementedError()

    def stop(self, force=False):
        """Ask the engine to stop the current measure.

        Parameters
        ----------
        force : bool, optional
            Force the engine to stop the performing the task. This allow the
            engine to use any means necessary to stop, in this case only should
            the call to this method block.

        """
        raise NotImplementedError()

    def shutdown(self, force=False):
        """Ask the engine top stop completely.

        After a call to this method the engine may need to re-initialize a
        number of things before running the next measure.

        Parameters
        ----------
        force : bool, optional
            Force the engine to stop the performing the task. This allow the
            engine to use any means necessary to stop, in this case only should
            the call to this method block.

        """
        raise NotImplementedError()


class Engine(Declarative):
    """A declarative class for contributing an engine.

    Engine object can be contributed as extensions child to the 'engines'
    extension point of the 'ecpy.measure' plugin.

    The name member inherited from enaml.core.Object should always be set to an
    easily understandable name for the user.

    """
    #: Unique name used to identify the engine. Should be user understandable.
    id = d_(Unicode())

    #: Description of the engine
    description = d_(Unicode())

    @d_func
    def new(self, workbench, default=True):
        """Create a new instance of the engine.

        Parameters
        ----------
        workbench : Workbench
            Reference to the application workbench.

        default : bool
            Whether to use default parameters or not when creating the object.

        """
        raise NotImplementedError()

    @d_func
    def react_to_selection(self, workbench):
        """Take any necessary actions when the engine is selected.

        This method is called by the framework at the appropriate time.

        """
        pass

    @d_func
    def react_to_unselection(self, workbenc):
        """Take any necessary actions when the engine is unselected.

        This method is called by the framework at the appropriate time.

        """
        pass

    @d_func
    def contribute_to_workspace(self, workspace):
        """Add contributions to the workspace.

        This method is called by the framework only if the engine is selected
        and the workspace is active.

        """
        pass

    @d_func
    def clean_workspace(self, workspace):
        """Remove any contributions from the workspace.

        This method is called by the framework only the workspace is active and
        the engine is unselected.

        """
        pass
