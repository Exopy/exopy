# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Instrument manager plugin.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import logging
from functools import partial

from atom.api import Typed, List

from ..utils.plugin_tools import (HasPrefPlugin, ExtensionsCollector,
                                  DeclaratorsCollector,
                                  make_extension_validator)
from .user import InstrUser
from .stater import Starter
from .driver_decl import Driver
from .connections.base_connection import Connection
from .settings.base_settings import Settings

logger = logging.getLogger(__name__)

DRIVERS_POINT = 'ecpy.instruments.drivers'

STARTERS_POINT = 'ecpy.instruments.starters'

USERS_POINT = 'ecpy.instruments.users'

CONNECTIONS_POINT = 'ecpy.instruments.connections'

SETTINGS_POINT = 'ecpy.instuments.settings'


class InstrumentPlugin(HasPrefPlugin):
    """The instrument plugin manages the instrument drivers and their use.

    """
    #: List of instruments for which at least one driver is declared.
    instruments = List()

    #: List of registered intrument users.
    #: Only registered users can be granted the use of an instrument.
    users = List()

    #: List of registered instrument starters.
    starters = List()

    #: List of registered connection types.
    connections = List()

    #: List of registered settings.
    settings = List()

    def start(self):
        """Start the plugin lifecycle by collecting all contributions.

        """
        super(InstrumentPlugin, self).start()

        core = self.workbench.get_plugin('enaml.workbench.core')
        core.invoke_command('ecpy.app.errors.enter_error_gathering')

        checker = make_extension_validator(InstrUser, (), ('plugin_id'))
        self._users = ExtensionsCollector(workbench=self.workbench,
                                          point=USERS_POINT,
                                          ext_class=InstrUser,
                                          validate_ext=checker)
        self._users.start()

        checker = make_extension_validator(Starter,
                                           ('initialize', 'check_infos',
                                            'finalize'),
                                           ('id', 'description'))
        self._starters = ExtensionsCollector(workbench=self.workbench,
                                             point=STARTERS_POINT,
                                             ext_class=Starter,
                                             validate_ext=checker)
        self._starters.start()

        checker = make_extension_validator(Connection, ('new',),
                                           ('id', 'description'))
        self._connections = ExtensionsCollector(workbench=self.workbench,
                                                point=CONNECTIONS_POINT,
                                                ext_class=Connection,
                                                validate_ext=checker)
        self._connections.start()

        checker = make_extension_validator(Settings, ('new',),
                                           ('id', 'description'))
        self._settings = ExtensionsCollector(workbench=self.workbench,
                                             point=SETTINGS_POINT,
                                             ext_class=Settings,
                                             validate_ext=checker)
        self._settings.start()

        self._drivers = DeclaratorsCollector(workbench=self.workbench,
                                             point=DRIVERS_POINT,
                                             ext_class=Driver)
        self._drivers.start()

        for contrib in ('instruments', 'users', 'starters', 'connections',
                        'settings'):
            self._update_contribs(contrib, None)

        for contrib in ('instruments', 'users', 'starters', 'connections',
                        'settings'):
            getattr(self, '_'+contrib).observe('contributions',
                                               partial(self._update_contribs,
                                                       contrib))

        core.invoke_command('ecpy.app.errors.exit_error_gathering')

    def stop(self):
        """Stop the plugin and remove all observers.

        """
        for contrib in ('instruments', 'users', 'starters', 'connections',
                        'settings'):
            getattr(self, '_'+contrib).stop()

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Collector of drivers.
    _drivers = Typed(DeclaratorsCollector)

    #: Collector of users.
    _users = Typed(ExtensionsCollector)

    #: Collector of starters.
    _starters = Typed(ExtensionsCollector)

    #: Collectorsof connections.
    _connections = Typed(ExtensionsCollector)

    #: Collector of settings.
    _settings = Typed(ExtensionsCollector)

    def _update_contribs(self, name, change):
        """Update the list of available contributions (editors, engines, tools)
        when they change.

        """
        setattr(self, name, list(getattr(self, '_'+name).contributions))

# Collect drivers

# Collect connections

# Collect settings

# Collect starters

# Collect aliases

# Collect profiles


# Request driver profile starter triplet

# Explore drivers (by manufacturer or kind), connections, settings
