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

import os
import sys
import logging
from functools import partial
from collections import defaultdict

from atom.api import Typed, List, Dict
from enaml.application import deferred_call
from watchdog.observers import Observer

from ..utils.watchdog import SystematicFileUpdater
from ..utils.plugin_tools import (HasPrefPlugin, ExtensionsCollector,
                                  DeclaratorsCollector,
                                  make_extension_validator)
from .user import InstrUser
from .starters.base_starter import Starter
from .drivers.driver_decl import Driver
from .connections.base_connection import Connection
from .settings.base_settings import Settings
from .manufacturer_aliases import ManufacturerAlias
from .infos import ManufacturersHolder, ProfileInfos, validate_profile_infos

logger = logging.getLogger(__name__)

DRIVERS_POINT = 'ecpy.instruments.drivers'

STARTERS_POINT = 'ecpy.instruments.starters'

USERS_POINT = 'ecpy.instruments.users'

CONNECTIONS_POINT = 'ecpy.instruments.connections'

SETTINGS_POINT = 'ecpy.instruments.settings'

ALIASES_POINT = 'ecpy.instruments.manufacturer_aliases'


def validate_user(user):
    """Validate that the user does declare a validate method if its policy is
    releasable.

    """
    if not user.id:
        return False, 'InstrUser must provide an id.'
    if user.policy == 'releasable':
        member = user.release_profiles
        func = getattr(member, 'im_func', getattr(member, '__func__', None))
        o_func = (InstrUser.release_profiles if sys.version_info >= (3,) else
                  InstrUser.release_profiles.__func__)
        if not func or func is o_func:
            msg = ("InstrUser policy is releasable but it does not declare a"
                   " a release_profiles function.")
            return False, msg

    return True, ''


# TODO add a way to specify default values for settings from the preferences
class InstrumentManagerPlugin(HasPrefPlugin):
    """The instrument plugin manages the instrument drivers and their use.

    """
    #: List of the known instrument profile ids.
    profiles = List()

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

    #: Currently used profiles.
    #: This dict should be edited by user code.
    used_profiles = Dict()

    def start(self):
        """Start the plugin lifecycle by collecting all contributions.

        """
        super(InstrumentManagerPlugin, self).start()

        core = self.workbench.get_plugin('enaml.workbench.core')
        core.invoke_command('ecpy.app.errors.enter_error_gathering')

        core = self.workbench.get_plugin('enaml.workbench.core')
        state = core.invoke_command('ecpy.app.states.get',
                                    {'state_id': 'ecpy.app.directory'})

        i_dir = os.path.join(state.app_directory, 'instruments')
        # Create instruments subfolder if it does not exist.
        if not os.path.isdir(i_dir):
            os.mkdir(i_dir)

        p_dir = os.path.join(state.app_directory, 'profiles')
        # Create profiles subfolder if it does not exist.
        if not os.path.isdir(p_dir):
            os.mkdir(p_dir)

        self._profiles_folders = [p_dir]

        self._users = ExtensionsCollector(workbench=self.workbench,
                                          point=USERS_POINT,
                                          ext_class=InstrUser,
                                          validate_ext=validate_user)
        self._users.start()

        checker = make_extension_validator(Starter,
                                           ('initialize', 'check_infos',
                                            'finalize', 'reset'),
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

        checker = make_extension_validator(ManufacturerAlias, (),
                                           ('id', 'aliases',))
        self._aliases = ExtensionsCollector(workbench=self.workbench,
                                            point=ALIASES_POINT,
                                            ext_class=ManufacturerAlias,
                                            validate_ext=checker)
        self._aliases.start()

        self._drivers = DeclaratorsCollector(workbench=self.workbench,
                                             point=DRIVERS_POINT,
                                             ext_class=Driver)
        self._drivers.start()

        for contrib in ('users', 'starters', 'connections', 'settings'):
            self._update_contribs(contrib, None)

        err = False
        details = {}
        for d_id, d_infos in self._drivers.contributions.items():
            res, tb = d_infos.validate(self)
            if not res:
                err = True
                details[d_id] = tb

        if err:
            core.invoke_command('ecpy.app.errors.signal',
                                {'kind': 'ecpy.driver-validation',
                                 'details': details})
        # TODO providing in app a way to have a splash screen while starting to
        # let the user know what is going on would be nice

        # TODO handle dynamic addition of drivers by observing contributions
        # and updating the manufacturers infos accordingly.
        # should also observe manufacturer aliases

        self._refresh_profiles()

        self._bind_observers()

        core.invoke_command('ecpy.app.errors.exit_error_gathering')

    def stop(self):
        """Stop the plugin and remove all observers.

        """
        self._unbind_observers()

        for contrib in ('drivers', 'users', 'starters', 'connections',
                        'settings'):
            getattr(self, '_'+contrib).stop()

    def create_connection(self, connection_id, infos):
        """Create a connection and initialize it.

        Parameters
        ----------
        connection_id : unicode
            Id of the the connection to instantiate.

        infos : dict
            Dictionarry to use to initialize the state of the connection.

        Returns
        -------
        connection : BaseConnection
            Ready to use widget.

        """
        c_decl = self._connections.contributions[connection_id]
        return c_decl.new(self.workbench, infos)

    def create_settings(self, settings_id, infos):
        """Create a settings and initialize it.

        Parameters
        ----------
        settings_id : unicode
            Id of the the settings to instantiate.

        infos : dict
            Dictionarry to use to initialize the state of the settings.

        Returns
        -------
        connection : BaseSettings
            Ready to use widget.

        """
        s_decl = self._settings.contributions[settings_id]
        return s_decl.new(self.workbench, infos)

    def get_drivers(self, drivers):
        """Query drivers class and the associated starters.

        Parameters
        ----------
        drivers : list
            List of driver ids for which the matching class should be returned.

        Returns
        -------
        drivers : dict
            Requested drivers and associated starter indexed by id.

        missing : list
            List of ids which do not correspond to any known valid driver.

        """
        ds = self._drivers.contributions
        knowns = {d_id: ds[d_id] for d_id in drivers if d_id in ds}
        missing = list(set(drivers) - set(knowns))

        return {d_id: (infos.cls, self._starters.contributions[infos.starter])
                for d_id, infos in knowns.items()}, missing

    def get_profiles(self, user_id, profiles, try_release=True, partial=False):
        """Query profiles for use by a declared user.

        Parameters
        ----------
        user_id : unicode
            Id of the user which request the authorization to use the
            instrument.

        profiles : list
            Ids of the instrument profiles which are requested.

        try_release : bool, optional
            Should we attempt to release currently used profiles.

        partial : bool, optional
            Should only a subset of the requested profiles be returned if some
            profiles are not available.

        Returns
        -------
        profiles : dict
            Requested profiles as a dictionary.

        unavailable : list
            List of profiles that are not currently available and cannot be
            released.

        """
        if user_id not in self.users:
            raise ValueError('Unknown instrument user tried to query profiles')

        used = [p for p in profiles if p in self.used_profiles]
        unavailable = []
        if used:
            released = []
            if not try_release:
                unavailable = used
            else:
                used_by_owner = defaultdict(set)
                for p in used:
                    used_by_owner[self.used_profiles[p]].add(p)
                for o in list(used_by_owner):
                    user = self._users.contributions[o]
                    if user.policy == 'releasable':
                        to_release = used_by_owner[o]
                        r = user.release_profiles(self.workbench, to_release)
                        unavailable.extend(set(to_release) - set(r))
                        released.extend(r)
                    else:
                        unavailable.extend(used_by_owner[o])

        if unavailable and not partial:
            if released:
                used = {k: v for k, v in self.used_profiles.items()
                        if k not in released}
                self.used_profiles = used
            return {}, unavailable

        available = ([p for p in profiles if p not in unavailable]
                     if unavailable else profiles)

        with self.suppress_notifications():
            u = self.used_profiles
            self.used_profiles = {}
        u.update({p: user_id for p in available})
        self.used_profiles = u

        queried = {}
        for p in available:
            queried[p] = self._profiles[p]._config.dict()

        return queried, unavailable

    def release_profiles(self, user_id, profiles):
        """Release some previously acquired profiles.

        The user should not maintain any communication with the instruments
        whose profiles have been released after calling this method.

        Parameters
        ----------
        user_id : unicode
            Id of the user releasing the profiles.

        profiles : iterable
            Profiles (ids) which are no longer needed by the user.

        """
        self.used_profiles = {k: v for k, v in self.used_profiles.items()
                              if k not in profiles or v != user_id}

    def get_aliases(self, manufacturer):
        """List the known aliases of a manufacturer.

        Parameters
        ----------
        manufacturer : id
            Name of the manufacturer for which to return the aliases.

        Returns
        -------
        aliases : list[unicode]
            Known aliases of the manufacturer.

        """
        aliases = self._aliases.contributions.get(manufacturer, [])
        if aliases:
            aliases = aliases.aliases
        return aliases

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Collector of drivers.
    _drivers = Typed(DeclaratorsCollector)

    #: Collector for the manufacturer aliases.
    _aliases = Typed(ExtensionsCollector)

    #: Declared manufacturers storing the corresponding model infos.
    _manufacturers = Typed(ManufacturersHolder)

    #: Collector of users.
    _users = Typed(ExtensionsCollector)

    #: Collector of starters.
    _starters = Typed(ExtensionsCollector)

    #: Collector of connections.
    _connections = Typed(ExtensionsCollector)

    #: Collector of settings.
    _settings = Typed(ExtensionsCollector)

    #: List of folders in which to search for profiles.
    # TODO make that list editable and part of the preferences
    _profiles_folders = List()

    #: Mapping of profile name to profile infos.
    _profiles = Dict()

    #: Watchdog observer tracking changes to the profiles folders.
    _observer = Typed(Observer, ())

    def _update_contribs(self, name, change):
        """Update the list of available contributions (editors, engines, tools)
        when they change.

        """
        setattr(self, name, list(getattr(self, '_'+name).contributions))

    def _refresh_profiles(self):
        """List of profiles living in the profiles folders.

        """
        profiles = {}
        logger = logging.getLogger(__name__)
        for path in self._profiles_folders:
            if os.path.isdir(path):
                filenames = sorted(f for f in os.listdir(path)
                                   if f.endswith('.instr.ini') and
                                   (os.path.isfile(os.path.join(path, f))))

                for filename in filenames:
                    profile_path = os.path.join(path, filename)
                    # Beware redundant names are overwritten
                    name = filename[:-len('.instr.ini')]
                    # TODO should be delayed and lead to a nicer report
                    i = ProfileInfos(path=profile_path, plugin=self)
                    res, msg = validate_profile_infos(i)
                    if res:
                        profiles[name] = i
                    else:
                        logger.warn(msg)
            else:
                logger.warn('{} is not a valid directory'.format(path))

        self._profiles = profiles
        self.profiles = list(profiles)

    def _bind_observers(self):
        """Start the observers.

        """
        for contrib in ('users', 'starters', 'connections', 'settings'):
            callback = partial(self._update_contribs, contrib)
            getattr(self, '_'+contrib).observe('contributions', callback)

        for folder in self._profiles_folders:
            def update():
                deferred_call(self._refresh_profiles)
            handler = SystematicFileUpdater(update)
            self._observer.schedule(handler, folder, recursive=True)

        self._observer.start()

    def _unbind_observers(self):
        """Stop the observers.

        """
        for contrib in ('users', 'starters', 'connections', 'settings'):
            callback = partial(self._update_contribs, contrib)
            getattr(self, '_'+contrib).observe('contributions', callback)

        self._observer.unschedule_all()
        self._observer.stop()
        try:
            self._observer.join()
        except RuntimeError:
            pass

    def _default__manufacturers(self):
        """Delayed till this is first needed.

        """
        holder = ManufacturersHolder(plugin=self)
        valid_drivers = [d for d in self._drivers.contributions.values()]
        holder.update_manufacturers(valid_drivers)

        return holder
