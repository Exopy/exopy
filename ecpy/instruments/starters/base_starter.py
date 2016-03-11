# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Tool handling initializind/finalizing a driver.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Unicode
from enaml.core.api import Declarative, d_, d_func


class Starter(Declarative):
    """Object responsible initializind/finalizing a driver of a certain type.

    """
    #: Unique id identifying this starter.
    #: The usual format is top_level_package_name.starter_name
    id = d_(Unicode())

    #: Description of the starter action.
    description = d_(Unicode())

    @d_func
    def initialize(self, driver_cls, connection, settings):
        """Fully initialize a driver and open the communication channel.

        Parameters
        ----------
        driver_cls : type
            Class of the driver to initialize.

        connection : dict
            Connection information provided by the user.

        settings : dict
            Driver specififc settings provided by the user.

        Returns
        -------
        driver :
            Driver instance fully initilized and ready for communication.

        Raises
        ------
        InstrIOError :
            If the connection to the instrument could not be opened.

        """
        raise NotImplementedError()

    @d_func
    def check_infos(self, driver_cls, connection, settings):
        """Check that the provided information and settings allow to open
        the communication.

        Parameters
        ----------
        driver_cls : type
            Class of the driver to initialize.

        connection : dict
            Connection information provided by the user.

        settings : dict
            Driver specififc settings provided by the user.

        Returns
        -------
        result : bool
            Whether the system managed to open the communication.

        msg : unicode
            Message giving details about any issue which may have occured
            during the test.

        """
        raise NotImplementedError()

    @d_func
    def reset(self, driver):
        """Reset the instrument state after a possible alteration by the user.

        Typically this shold clear the cache of the driver and reset any notion
        of ownership.

        """
        raise NotImplementedError()

    @d_func
    def finalize(self, driver):
        """Close the communication with the instrument.

        Parameters
        ----------
        driver :
            Driver instance created previously by the starter.

        """
        raise NotImplementedError()
