# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Declaration of plugin susceptible to use instruments

"""
from atom.api import Enum, Unicode
from enaml.core.declarative import Declarative, d_, d_func


class InstrUser(Declarative):
    """Extension to the 'exopy.instruments.users' extensions point.

    """
    #: Plugin id associated with this use of instrument. This allow the manager
    #: to know what part of the application requested the right to use some
    #: drivers.
    id = d_(Unicode())

    #: Is the plugin susceptible to release the profiles it is currently using
    #: if the manager asks it to do so.
    policy = d_(Enum('releasable', 'unreleasable'))

    @d_func
    def release_profiles(self, workbench, profiles):
        """Release the specified profiles or some of them.

        This call can block until the profiles can be released (if it is likely
        to happen in a relatively short time). The
        'exopy.instruments.notify_profiles_released' command should not be
        called (the manager knows what profiles it requested and will handle
        the tracking of the current user for each profile itself).

        Parameters
        ----------
        workbench :
            Application workbench.

        profiles : list[unicode]
            List of profiles the manager is requesting the user to release.

        Returns
        -------
        released_profiles : list[unicode]
            List of the profiles that have been released.

        """
        raise NotImplementedError()
