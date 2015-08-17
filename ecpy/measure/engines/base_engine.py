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

from atom.api import Atom, Bool, Unicode, ForwardTyped, Signal
from enaml.core.api import Declarative, d_, d_func


class BaseEngine(Atom):
    """Base class for all engines.

    """
    #: Declaration defining this engine.
    declaration = ForwardTyped(lambda: Engine)

    #: Signal used to pass news about the measurement progress.
    news = Signal()

    #: Event through which the engine signals it is done with a measure.
    completed = Signal()

    #: Bool representing the current state of the engine.
    active = Bool()

    def prepare_to_run(self, name, root, monitored_entries, build_deps):
        """Make the engine ready to perform a measure.

        This method should not start the engine.

        Parameters
        ----------
        name : unicode
            Name of the measure.

        root : RootTask
            The root task representing the measure to perform.

        monitored_entries : iterable
            The database entries to observe. Any change of one of these entries
            should be notified by the news event.

        build_deps : dict
            Dict holding the build dependencies of the task.

        """
        raise NotImplementedError()

    def perform(self, task):
        """Execute a given task hierarchy.

        This is needed for pre and post execution hook needing to execute
        arbitrary tasks.

        """
        raise NotImplementedError()

    def run(self):
        """Start the execution of the measure by the engine.

        This method must not wait for the measure to complete to return.

        """
        raise NotImplementedError()

    def pause(self):
        """Ask the engine to pause the current measure.

        This method should not wait for the measure to pause to return.
        When the pause is effective the engine should add pause to the plugin
        flags.

        """
        raise NotImplementedError()

    def resume(self):
        """Ask the engine to resume the currently paused measure.

        This method should not wait for the measure to resume.
        Thsi method should remove the 'paused' flag from the plugin flags.

        """
        raise NotImplementedError()

    def stop(self):
        """Ask the engine to stop the current measure.

        This method should not wait for the measure to stop.

        """
        raise NotImplementedError()

    def exit(self):
        """Ask the engine top stop completely.

        After a call to this method the engine may need to re-initialize a
        number of things before running the next measure. This method should
        not wait for the engine to exit.

        """
        raise NotImplementedError()

    def force_stop(self):
        """Force the engine to stop the current measure.

        This method should stop the measure no matter what is going on. It can
        block.

        """
        raise NotImplementedError()

    def force_exit(self):
        """Force the engine to exit.

        This method should stop the process no matter what is going on. It can
        block.

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
    def new(self, workbench):
        """Create a new instance of the engine.

        Parameters
        ----------
        workbench : Workbench
            Reference to the application workbench.

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
