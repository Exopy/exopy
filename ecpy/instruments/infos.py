# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Container objects used to encapsulate info about drivers, instruments, etc

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from collection import defaultdict
from itertools import chain

from atom.api import (Atom, Unicode, Dict, Callable, List, Property, Typed,
                      Bool, Enum, Value)

from ..utils.mapping_utils import recursive_update


INSTRUMENT_KINDS = ('Other', 'DC source', 'AWG', 'RF source', 'Lock-in',
                    'Spectrum analyser', 'Multimeter')


class DriverInfos(Atom):
    """Object summarizing the information about a driver.

    """
    #: Id of the driver built on the class name and the top-level package
    id = Unicode()

    #: Actual class to use as driver.
    cls = Callable()

    #: Infos allowing to identify the instrument this driver is targetting.
    infos = Dict()

    #: Starter id
    starter = Unicode()

    #: Connection information.
    connections = Dict()

    #: Settings information.
    settings = Dict()

    # XXXX Need to determine when to call this
    def validate(self, plugin):
        """Validate that starter, connections, settings ids are all known.

        Parameters
        ----------
        plugin :
            Instrument plugin instance holding the starters (connections,
            settings) definitions.

        Returns
        -------
        result : bool
            Boolean indicating if all ids are indeed known.

        unknown : dict
            Mapping listing by categories (starter, connections, settings) the
            unkown ids.

        """
        result = True
        unknown = defaultdict(set)

        if self.starter not in plugin.starters:
            result = False
            unknown['starter'].add(self.starter)

        for k in self.connections.keys():
            if k not in plugin.connections:
                result = False
                unknown['connections'].add(k)

        for k in self.settings.keys():
            if k not in plugin.settings:
                result = False
                unknown['settings'].add(k)

        return result, unknown


# TODO the construction of the hierarchy Manufacturer/Serie/Model/Drivers may
# become quite time consuming and making the creation of each one of those
# lazy may help...


class InstrumentModelInfos(Atom):
    """Details about a particular model based on all the available drivers.

    """
    #: Instrument manufacturer (this is the real manufacturer not an alias).
    manufacturer = Unicode()

    #: Instrument model.
    model = Unicode()

    #: Instrument serie.
    serie = Unicode()

    #: Instrument kind.
    kind = Enum(*INSTRUMENT_KINDS)

    #: List of supported drivers.
    drivers = List()

    #: Supported connections (all drivers connections infos are merged).
    connections = Dict()

    #: Supported settings (all drivers settings infos are merged).
    settings = Dict()

    #: Id of the model.
    id = Property(cached=True)

    def update(self, drivers, removed=False):
        """Update the infos from a list of drivers.

        """
        if not removed:
            for d in drivers:
                recursive_update(self.connections, d.connections)
                recursive_update(self.settings, d.settings)
            self.drivers.extend(drivers)
        else:
            self.drivers = [d for d in self.drivers if d not in drivers]
            if self.drivers:
                self.connections = {}
                self.settings = {}
                for d in self.drivers:
                    recursive_update(self.connections, d.connections)
                    recursive_update(self.settings, d.settings)

    def find_matching_drivers(self, connection_id, settings_id=None):
        """Find the matching driver implementation.

        Parameters
        ----------
        connection_id : unicode
            Connection id for which to for a matching driver.

        settings_id : unicode, optional
            Settings id for which to find a matching id.

        """
        drivers = [d for d in self.drivers if connection_id in d.connections]
        if settings_id:
            drivers = [d for d in drivers if settings_id in d.settings]
        return drivers

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    def _get_id(self):
        """Getter for the id property.

        """
        return self.manufacturer + '.' + self.model


class SeriesInfos(Atom):
    """Container object used to store series infos.

    """
    #: Name of the serie.
    name = Unicode()

    #: List of all declared instrument models.
    #: This object should not be manipulated by user code.
    instruments = List()

    #: Expose the known instruments only of the matching kind.
    kind = Unicode('All')

    def update_models(self, drivers, removed=False):
        """Update the known models from a list of drivers.

        """
        models_d = defaultdict(set)
        for d in drivers:
            models_d[d.infos['model']].add(d)

        for m in models_d:
            if m not in self._models:
                if removed:
                    return
                di = list(models_d[m])[0].infos
                i = InstrumentModelInfos(manufacturer=di['manufacturer'],
                                         serie=di['serie'],
                                         model=di['model'],
                                         kind=di['kind'])
                self._models[m] = i
            i = self._models[m]
            i.update(models_d[m], removed)
            if removed and not i.drivers:
                del self._models[m]
            self._list_instruments()

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: All known instrument models.
    _models = Dict()

    def _post_setattr_kind(self, old, new):
        """Regenerate the list of models.

        """
        self.instruments = self._list_instruments()

    def _list_instruments(self, models):
        """List all the known models matching the expected kind.

        Parameters
        ----------

        """
        return filter(lambda x: x.kind == self.kind
                      if self.kind != 'All' else None, models)


class ManufacturerInfos(SeriesInfos):
    """Container object used to store manufacturer infos.

    Notes
    -----
    Models are stored by series in instruments member if use_series is True

    """
    #: Expose the known instrument by series.
    use_series = Bool(True)

    #: Known aliases for the manufacturer.
    aliases = List()

    def update_series_and_models(self, drivers, removed):
        """Update the known series and models from a list of drivers.

        """
        series_d = defaultdict(set)
        for d in drivers:
            series_d[d.infos['serie']].add(d)

        for s, ds in series_d.items():
            if s == '':
                self.update_models(ds, removed)
            else:
                if s not in self._series:
                    if removed:
                        continue
                    self._series[s] = SeriesInfos(kind=self.kind, name=s)
                serie = self._series[s]
                serie.update_models(ds, removed)
                if removed and not serie._models:
                    del self._series[s]

        self.instruments = self._list_instruments()

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: All known series for this manufacturer.
    _series = Dict()

    def _post_setattr_use_series(self, old, new):
        """Update the list of models when the usage of series is modified.

        """
        self._list_instruments(())

    def _post_setattr_kind(self, old, new):
        """Regenerate the list of models.

        """
        for s in self.series:
            s.kind = new
        super(ManufacturerInfos, self)._post_setattr_kind(old, new)

    def _list_instruments(self, models):
        """Build the list of models using either series or not.

        """
        if not self.use_series:
            models = chain(self._models,
                           *[s.instruments for s in self.series.values()])
            return super(ManufacturerInfos, self)._list_instruments(models)
        else:
            models = super(ManufacturerInfos, self)._list_instruments()
            return [s for s in self.series.values() if s.instruments] + models


class ManufacturerHolder(Atom):
    """Container class for manufacturers.

    """
    #: Filtered list of manufacturers.
    manufacturers = List()

    #: Expose the known instrument by series.
    use_series = Bool(True)

    #: Expose the known instruments only of the matching kind.
    kind = Unicode('All')

    def update_manufacturer(self, drivers, removed=False):
        """Update a manufacturer infos and create it if it does not exist yet.

        Parameters
        ----------
        drivers : list
            List of drivers sharing a common manufacturer.

        """
        m = drivers[0].infos['manufacturer']
        if m not in self._manufacturers:
            if removed:
                return
            self._manufacturers[m] = \
                ManufacturerInfos(name=m, kind=self.kind,
                                  use_series=self.use_series)

        manufacturer = self._manufacturers[m]
        manufacturer.update_series_and_models(drivers, removed)
        if removed and not manufacturer._series and not manufacturer._models:
            del self._manufacturers[m]

        self._list_manufacturers()

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: All known manufacturers.
    _manufacturers = Dict()

    def _post_setattr_kind(self, old, new):
        """Regenerate the list of models.

        """
        for m in self._manufacturers.values():
            m.kind = new
        self._list_manufacturers()

    def _post_setattr_use_series(self, old, new):
        """Regenerate the list of models.

        """
        for m in self._manufacturers.values():
            m.use_series = new
        self._list_manufacturers()

    def _list_manufacturers(self):
        """Make available only the manufacturers whose at least one model fit
        the search criterias.

        """
        self.manufacturers = filter(lambda m: m.instruments,
                                    self._manufacturers.values())


class ProfileInfos(Atom):
    """Details about a profile.

    This is used as a cache to avoid reloading all the profile everytime.

    """
    #: Path to the .ini file holding the full infos.
    path = Unicode()

    #: Reference to the instrument plugin.
    plugin = Value()

    #: Profile id.
    id = Unicode()

    #: Supported model
    model = Typed(InstrumentModelInfos)

    #: Names of the connections
    connections = List()

    #: names of the settings
    settings = List()

    def update_profile(self, profile_dict):
        """
        """
        pass

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: ConfigObj object associated to the profile.
    _config = Value()

    def _default_model(self):
        """
        """
        pass

    def _default_connections(self):
        """
        """
        pass

    def _default_settings(self):
        """
        """
        pass

    def _default__config(self):
        """
        """
        pass
