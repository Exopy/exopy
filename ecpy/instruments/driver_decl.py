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

from atom.api import Atom, Unicode, Enum, Dict, Value
from enaml.core.api import d_
from future.utils import python_2_unicode_compatible

from ..utils.declarator import Declarator, GroupDeclarator, import_and_get


INSTRUMENT_KINDS = ('Other', 'DC source', 'AWG', 'RF source', 'Lock-in',
                    'Spectrum analyser', 'Multimeter')


@python_2_unicode_compatible
class Driver(Declarator):
    """Declarator used to register a new driver for an instrument.

    """
    #: Path to the driver object. Path should be dot separated and the class
    #: name preceded by ':'.
    #: XXXX complete : ex: ecpy_hqc_legacy.instruments.
    #: The path of any parent Drivers object will be prepended to it.
    driver = d_(Unicode())

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

    def register(self):
        """
        """
        pass

    def unregister(self):
        """
        """
        pass

    def __str__(self):
        """Identify the decl by its members.

        """
        members = ('path', 'manufacturer', 'serie', 'model', 'kind', 'starter',
                   'connections', 'settings')
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


@python_2_unicode_compatible
class Drivers(GroupDeclarator):
    """Declarator to group driver declarations.

    For the full documentation of the members values please the Driver class.

    """
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
        members = ('path', 'manufacturer', 'serie', 'kind', 'starter',
                   'connections', 'settings')
        st = '{} whose known members are :\n{}\n and declaring :\n{}'
        st_m = '\n'.join(' - {} : {}'.format(m, v)
                         for m, v in [(m, getattr(self, m)) for m in members
                                      if getattr(self, m)]
                         )
        return st.format(type(self).__name__, st_m,
                         '\n'.join(' - {}'.format(c) for c in self.children))


class DriverInfos(Atom):
    """Object summarizing the information about a driver.

    """
    #: Actual class to use as driver.
    driver = Value()

    #: INfos allowing to identify the instrument this driver is targetting.
    infos = Dict()

    #: Connection information.
    connections = Dict()

    #: Settings information.
    settings = Dict()

    def validate(self, plugin, kind):
        """
        """
        # validate that the connections, settings, starter make sense
        # better to delay to first use of infos so that we know that we should
        # have access to everything by that time.
        pass
