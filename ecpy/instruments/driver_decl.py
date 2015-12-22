# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Declarator for registering drivers.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Unicode, Enum, Value, Dict
from enaml.core.api import d_, Declarative


class Driver(Declarative):
    """Base class to declare a driver.

    A Driver can accept declarative children specifying the connections
    supported by the driver (BaseConnection) or the possible global settings
    associated with the driver.

    """
    #: Path to the driver object. Path should be dot separated and the class
    #: name preceded by ':'.
    #: XXXX complete : ex: ecpy_hqc_legacy.instruments.
    #: The path of any parent GroupDeclarator object will be prepended to it.
    driver = d_(Unicode())

    #: Name of the instrument manufacturer.
    manufacturer = d_(Unicode())

    #: Serie this instrument is part of. This is optional as it does not always
    #: make sense to be specified but in some cases it can help finding a
    #: a driver.
    serie = d_(Unicode())

    #: Model of the instrument this driver has been written for.
    model = d_(Unicode())

    #: Kind of the instrument, to ease instrument look up. If no kind match,
    #: leave 'Other' as the kind.
    kind = d_(Enum('Other', 'DC source', 'AWG', 'RF source', 'Lock-in',
                   'Spectrum analyser', 'Multimeter'))

    #: Starter to use when initializing/finialzing this driver. By default this
    #: is inferred from the class of the driver, specifying this value
    #: overwrites the default.
    starter = d_(Unicode())

    #: Supported connections and default values for some parameters. The
    #: admissible values for a given kind can be determined by looking at the
    #: Connection object whose id match. (This can be done in the application
    #: Instruments->Connections.)
    #: ex : {'visa_tcpip' : {'port': 7500, 'resource_class': 'SOCKET'}}¯
    connections = d_(Dict())

    #: Special settings for the driver, not fitting the connections. Multiple
    #: identical connection infos with different settings can co-exist in a
    #: profile. The admissible values for a given kind can be determined by
    #: looking at the Settings object whose id match. (This can be done in the
    #: application Instruments->Settings.)
    #: ex : {'lantz': {'resource_manager': '@py'}}
    settings = d_(Dict())

    def get_driver(self):
        """Return the actual class this declaration refers to.

        """
        if not self._driver:
            pass  # XXXX add import logic and error reporting (exception)

        return self._driver

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Reference to the class pointed by driver.
    _driver = Value()
