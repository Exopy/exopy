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

from traceback import format_exc

from atom.api import Unicode, Enum, Dict, Property
from enaml.core.api import d_
from future.utils import python_2_unicode_compatible

from ...utils.declarator import Declarator, GroupDeclarator, import_and_get
from ..infos import DriverInfos, INSTRUMENT_KINDS


@python_2_unicode_compatible
class Driver(Declarator):
    """Declarator used to register a new driver for an instrument.

    """
    #: Path to the driver object. Path should be dot separated and the class
    #: name preceded by ':'.
    #: TODO complete : ex: ecpy_hqc_legacy.instruments.
    #: The path of any parent Drivers object will be prepended to it.
    driver = d_(Unicode())

    #: Name identifying the system the driver is built on top of (lantz, hqc,
    #: slave, etc ...). Allow to handle properly multiple drivers declared in
    #: a single extension package for the same instrument.
    architecture = d_(Unicode())

    #: Name of the instrument manufacturer. Can be inferred from parent
    #: Drivers.
    manufacturer = d_(Unicode())

    #: Serie this instrument is part of. This is optional as it does not always
    #: make sense to be specified but in some cases it can help finding a
    #: a driver. Can be inferred from parent Drivers.
    serie = d_(Unicode())

    #: Model of the instrument this driver has been written for.
    model = d_(Unicode())

    #: Kind of the instrument, to ease instrument look up. If no kind match,
    #: leave 'Other' as the kind. Can be inferred from parent
    #: Drivers.
    kind = d_(Enum(*INSTRUMENT_KINDS))

    #: Starter to use when initializing/finialzing this driver.
    #: Can be inferred from parent Drivers.
    starter = d_(Unicode())

    #: Supported connections and default values for some parameters. The
    #: admissible values for a given kind can be determined by looking at the
    #: Connection object whose id match. (This can be done in the application
    #: Instruments->Connections.)
    #: ex : {'visa_tcpip' : {'port': 7500, 'resource_class': 'SOCKET'}}
    #: Can be inferred from parent Drivers.
    connections = d_(Dict())

    #: Special settings for the driver, not fitting the connections. Multiple
    #: identical connection infos with different settings can co-exist in a
    #: profile. The admissible values for a given kind can be determined by
    #: looking at the Settings object whose id match. (This can be done in the
    #: application Instruments->Settings.)
    #: ex : {'lantz': {'resource_manager': '@py'}}
    #: Can be inferred from parent Drivers.
    settings = d_(Dict())

    #: Id of the driver computed from the top-level package and the driver name
    id = Property(cached=True)

    def register(self, collector, traceback):
        """Collect driver and add infos to the DeclaratorCollector
        contributions member.

        """
        # Build the driver id by assembling the package name, the architecture
        # and the class name
        driver_id = self.id

        # Determine the path to the task and view.
        path = self.get_path()
        try:
            d_path, driver = (path + '.' + self.driver
                              if path else self.driver).split(':')
        except ValueError:
            msg = 'Incorrect %s (%s), path must be of the form a.b.c:Class'
            traceback[driver_id] = msg
            return

        # Check that the driver does not already exist.
        if driver_id in collector.contributions or driver_id in traceback:
            i = 1
            while True:
                err_id = '%s_duplicate%d' % (driver_id, i)
                if err_id not in traceback:
                    break

            msg = 'Duplicate definition of {}, found in {}'
            traceback[err_id] = msg.format(self.architecture + '.' + driver,
                                           d_path)
            return

        meta_infos = {k: getattr(self, k)
                      for k in ('architecture', 'manufacturer', 'serie',
                                'model', 'kind')
                      }
        infos = DriverInfos(id=driver_id,
                            infos=meta_infos,
                            starter=self.starter,
                            connections=self.connections,
                            settings=self.settings)

        # Get the driver class.
        d_cls = import_and_get(d_path, driver, traceback, driver_id)
        if d_cls is None:
            return

        try:
            infos.cls = d_cls
        except TypeError:
            msg = '{} should a callable.\n{}'
            traceback[driver_id] = msg.format(d_cls, format_exc())
            return

        collector.contributions[driver_id] = infos

        self.is_registered = True

    def unregister(self, collector):
        """Remove contributed infos from the collector.

        """
        if self.is_registered:

            # Remove infos.
            driver_id = self.id
            try:
                del collector.contributions[driver_id]
            except KeyError:
                pass

            self.is_registered = False

    def __str__(self):
        """Identify the decl by its members.

        """
        members = ('driver', 'architecture', 'manufacturer', 'serie', 'model',
                   'kind', 'starter', 'connections', 'settings')
        st = '{} whose known members are :\n{}'
        st_m = '\n'.join(' - {} : {}'.format(m, v)
                         for m, v in [(m, getattr(self, m)) for m in members]
                         )
        return st.format(type(self).__name__, st_m)

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    def _default_manufacturer(self):
        """Default value grabbed from parent if not provided explicitely.

        """
        return self._get_inherited_member('manufacturer')

    def _default_serie(self):
        """Default value grabbed from parent if not provided explicitely.

        """
        return self._get_inherited_member('serie')

    def _default_kind(self):
        """Default value grabbed from parent if not provided explicitely.

        """
        return self._get_inherited_member('kind')

    def _default_starter(self):
        """Default value grabbed from parent if not provided explicitely.

        """
        return self._get_inherited_member('starter')

    def _default_connections(self):
        """Default value grabbed from parent if not provided explicitely.

        """
        return self._get_inherited_member('connections')

    def _default_settings(self):
        """Default value grabbed from parent if not provided explicitely.

        """
        return self._get_inherited_member('settings')

    def _get_inherited_members(self, member, parent=None):
        """Get the value of a member found in a parent declarator.

        """
        parent = parent or self.parent
        if isinstance(parent, Drivers):
            value = getattr(parent, member)
            if value is not None:
                return value
            else:
                return self._get_inherited_members(member, parent.parent)

    def _get_id(self):
        """Create the unique identifier of the driver using the top level
        package the architecture and the class name.

        """
        if ':' in self.driver:
            path = self.get_path()
            d_path, d = (path + '.' + self.driver
                         if path else self.driver).split(':')

            # Build the driver id by assembling the package name and the class
            # name
            return '.'.join((d_path.split('.', 1)[0], self.architecture, d))

        else:
            return self.driver


@python_2_unicode_compatible
class Drivers(GroupDeclarator):
    """Declarator to group driver declarations.

    For the full documentation of the members values please the Driver class.

    """
    #: Name identifying the system the driver is built on top of for the
    #: declared children.
    architecture = d_(Unicode())

    #: Instrument manufacturer of the declared children.
    manufacturer = d_(Unicode())

    #: Serie of the declared children.
    serie = d_(Unicode())

    #: Kind of the declared children.
    kind = d_(Enum(*INSTRUMENT_KINDS))

    #: Starter to use for the declared children.
    starter = d_(Unicode())

    #: Supported connections of the declared children.
    connections = d_(Dict())

    #: Settings of the declared children.
    settings = d_(Dict())

    def __str__(self):
        """Identify the group by its mmebers and declared children.

        """
        members = ('path', 'architecture', 'manufacturer', 'serie', 'kind',
                   'starter', 'connections', 'settings')
        st = '{} whose known members are :\n{}\n and declaring :\n{}'
        st_m = '\n'.join(' - {} : {}'.format(m, v)
                         for m, v in [(m, getattr(self, m)) for m in members
                                      if getattr(self, m)]
                         )
        return st.format(type(self).__name__, st_m,
                         '\n'.join(' - {}'.format(c) for c in self.children))
