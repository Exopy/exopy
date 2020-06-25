# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Base classes for all engines

"""
from atom.api import (Atom, Str, ForwardTyped, Signal, Enum, Bool, Dict,
                      Value, List)
from enaml.core.api import Declarative, d_, d_func


class ExecutionInfos(Atom):
    """Information necessary for engine to execute a task.

    This object is also used by the engine to provide feedback about the
    execution of the task.

    """
    #: Id used to identify the task in logger messages.
    id = Str()

    #: Task to execute.
    task = Value()

    #: Build dependencies. This allow to rebuild the task if necessary.
    build_deps = Dict()

    #: Runtime dependencies of the task.
    runtime_deps = Dict()

    #: List of entries for which the engine should send updates during
    #: processing.
    observed_entries = List()

    #: Boolean indicating whether the engine should run the checks of the task.
    checks = Bool(True)

    #: Boolean set by the engine, indicating whether or not the task was
    #: successfully executed.
    success = Bool()

    #: Errors which occured during the execution of the task if any.
    errors = Dict()


class BaseEngine(Atom):
    """Base class for all engines.

    """
    #: Declaration defining this engine.
    declaration = ForwardTyped(lambda: Engine)

    #: Current status of the engine.
    status = Enum('Stopped', 'Waiting', 'Running', 'Pausing', 'Paused',
                  'Resuming', 'Stopping', 'Shutting down')

    #: Signal used to pass news about the measurement progress.
    progress = Signal()

    def perform(self, exec_infos):
        """Execute a given task and catch any error.

        Parameters
        ----------
        exec_infos : ExecutionInfos
            TaskInfos object describing the work to expected of the engine.

        Returns
        -------
        exec_infos : ExecutionInfos
            Input object whose values have been updated. This is simply a
            convenience.

        """
        raise NotImplementedError()

    def pause(self):
        """Ask the engine to pause the execution.

        This method should not wait for the task to pause to return.
        When the pause is effective the engine should signal it by updating its
        status.

        """
        raise NotImplementedError()

    def resume(self):
        """Ask the engine to resume the execution.

        This method should not wait for the measurement to resume.
        When the pause is over the engine should signal it by updating its
        status.

        """
        raise NotImplementedError()

    def stop(self, force=False):
        """Ask the engine to stop the execution.

        This method should not wait for the execution to stop save if a forced
        stop was requested.

        Parameters
        ----------
        force : bool, optional
            Force the engine to stop the performing the task. This allow the
            engine to use any means necessary to stop, in this case only should
            the call to this method block.

        """
        raise NotImplementedError()

    def shutdown(self, force=False):
        """Ask the engine to stop completely.

        After a call to this method the engine may need to re-initialize a
        number of things before running the next task.
        This method should not wait for the engine to shutdown save if a
        forced stop was requested.

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
    extension point of the 'exopy.measurement' plugin.

    The name member inherited from enaml.core.Object should always be set to an
    easily understandable name for the user.

    """
    #: Unique name used to identify the engine. Should be user understandable.
    id = d_(Str())

    #: Description of the engine
    description = d_(Str())

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
    def react_to_unselection(self, workbench):
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
