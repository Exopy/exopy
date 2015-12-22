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

from atom.api import Unicode, Value
from enaml.core.api import Declarative, d_, d_func


class Starter(Declarative):
    """Object responsible initializind/finalizing a driver of a certain type.

    """
    #: Unique id identifying this starter.
    #: The usual format is top_level_package_name.tool_name
    id = d_(Unicode())

    #: Description of the starter action.
    description = d_(Unicode())

    #:
    base_type = d_(Value())

    @d_func
    def initialize(self, driver_cls, connection, settings):
        """Fully initialize a driver and prepare the communication.

        Parameters
        ----------
        driver_cls : type

        connection :

        settings :

        Returns
        -------
        driver :

        """
        raise NotImplementedError()

    @d_func
    def check_infos(self, driver_cls, connection, settings):
        """

        Parameters
        ----------
        driver_cls : type

        connection :

        settings :

        Returns
        -------
        driver :

        """
        raise NotImplementedError()

    @d_func
    def finalize(self, driver):
        """

        Parameters
        ----------
        driver :

        """
        raise NotImplementedError()
