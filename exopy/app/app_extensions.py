# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""App plugin extensions declarations.

"""
from atom.api import Unicode, Int
from enaml.core.api import Declarative, d_, d_func


class AppStartup(Declarative):
    """A declarative class for defining a workbench app start-up contribution.

    AppStartup object can be contributed as extensions child to the 'startup'
    extension point of the 'exopy.app' plugin. AppStartup object are used
    to customize the application start up.

    """
    #: The globally unique identifier for the start-up.
    id = d_(Unicode())

    #: The priority determine the order in which AppStartup are called. The
    #: **lowest** this number the sooner the object will be called. Two
    #: AppStartup with the same priority are called in the order in which they
    #: have been discovered.
    priority = d_(Int(20))

    @d_func
    def run(self, workbench, cmd_args):
        """Function called during app start-up.

        Parameters
        ----------
        workbench :
            Reference to the application workbench.

        cmd_args :
            Commandline arguments passed by the user.

        """
        pass


class AppClosing(Declarative):
    """A declarative class for defining a workbench app closing contribution.

    AppClosing object can be contributed as extensions child to the 'closing'
    extension point of the 'exopy.app' plugin. AppClosing object are used
    to check whether or not the application can be exited safely.

    Attributes
    ----------
    id : unicode
        The globally unique identifier for the closing.

    validate : callable(window, event)
        A callable performing checks ensuring that the application can be
        safely exited and setting the event (CloseEvent) accordingly.

    """
    #: The globally unique identifier for the closing.
    id = d_(Unicode())

    @d_func
    def validate(self, window, event):
        """Check that the application can be safely exited.

        If it is not the case the event should be ignored (by calling the
        ignore method)

        Parameters
        ----------
        window :
            Reference to the main application window.

        event : enaml.widgets.window.ClosedEvent
            Closing event whose ignore method should be called to prevent
            application closing.

        """
        pass


class AppClosed(Declarative):
    """A declarative class for defining a workbench app closed contribution.

    AppClosed object can be contributed as extensions child to the 'closed'
    extension point of the 'exopy.app' plugin. AppClosed object are used
    to perform some clean up operation before stopping any plugin.

    MOST of the time performing clean up when stopping the plugin is sufficient
    and should be the preferred solution.

    Attributes
    ----------
    id : unicode


    validate : callable(window, event)
        A callable performing checks ensuring that the application can be
        safely exited and setting the event (CloseEvent) accordingly.

    """
    #: The globally unique identifier for the closing.
    id = d_(Unicode())

    #: The priority determine the order in which AppClosed are called. The
    #: **lowest** this number the sooner the object will be called. Two
    #: AppClosed with the same priority are called in the order in which they
    #: have been discovered.
    priority = d_(Int(20))

    @d_func
    def clean(self, workbench):
        """Function called during application closing.

        Parameters
        ----------
        workbench :
            Reference to the application workbench.

        """
        pass
