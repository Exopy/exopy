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

from collections import defaultdict
from itertools import chain
from operator import attrgetter

from configobj import ConfigObj
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

    #: Flag indicating whether or not the informations stored are valid
    #: and safe to use.
    valid = Bool()

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

        self.valid = result

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

        Parameters
        ----------
        drivers : list[DriverInfos]
            List of drivers infos to use for updating.

        remove : bool, optional
            Flag indicating whether the infos should be added or removed.

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
        """Find the drivers supporting the right connection and settings.

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
        parts = [self.manufacturer, self.model]
        if self.serie:
            parts.insert(1, self.serie)
        return '.'.join(parts)


class SeriesInfos(Atom):
    """Container object used to store series infos.

    """
    #: Name of the serie.
    name = Unicode()

    #: List of the instrument models matching the selected kind.
    #: This object should not be manipulated by user code.
    instruments = List()

    #: Expose the known instruments only of the matching kind.
    kind = Enum('All', *INSTRUMENT_KINDS)

    def update_models(self, drivers, removed=False):
        """Update the known models from a list of drivers.

        """
        models_d = defaultdict(set)
        for d in drivers:
            models_d[d.infos['model']].add(d)

        for m in models_d:
            if m not in self._models:
                if removed:
                    continue
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

        self.instruments = self._list_instruments(self._models.values())

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: All known instrument models.
    _models = Dict()

    def _post_setattr_kind(self, old, new):
        """Regenerate the list of models.

        """
        self.instruments = self._list_instruments(self._models.values())

    def _list_instruments(self, models):
        """List all the models matching the expected kind.

        """
        if self.kind == 'All':
            return sorted(models, key=attrgetter('model'))
        else:
            ms = [m for m in models if m.kind == self.kind]
            ms.sort(key=attrgetter('model'))
            return ms


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

    def update_series_and_models(self, drivers, removed=False):
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

        self.instruments = self._list_instruments(self._models)

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: All known series for this manufacturer.
    _series = Dict()

    def _post_setattr_use_series(self, old, new):
        """Update the list of models when the usage of series is modified.

        """
        self.instruments = self._list_instruments(())

    def _post_setattr_kind(self, old, new):
        """Regenerate the list of models.

        """
        for s in self._series.values():
            s.kind = new
        super(ManufacturerInfos, self)._post_setattr_kind(old, new)

    def _list_instruments(self, models):
        """Build the list of models using either series or not.

        """
        if not self.use_series:
            models = chain(self._models.values(),
                           *[s.instruments for s in self._series.values()])
            return super(ManufacturerInfos, self)._list_instruments(models)
        else:
            models = super(ManufacturerInfos,
                           self)._list_instruments(self._models.values())
            series = [s for s in self._series.values() if s.instruments]
            series.sort(key=attrgetter('name'))
            return series + models


class ManufacturersHolder(Atom):
    """Container class for manufacturers.

    """
    #: Refrence to the instrument plugin.
    plugin = Value()

    #: Filtered list of manufacturers.
    manufacturers = List()

    #: Expose the known instrument by series.
    use_series = Bool(True)

    #: Expose the known instruments only of the matching kind.
    kind = Unicode('All')

    def update_manufacturers(self, drivers, removed=False):
        """Update a manufacturer infos and create it if it does not exist yet.

        Parameters
        ----------
        drivers : list
            List of drivers.

        """
        aliases = {a: o
                   for o, m_a in self.plugin._aliases.contributions.items()
                   for a in m_a.aliases}

        manufacturers = defaultdict(list)
        for d in drivers:
            m = d.infos['manufacturer']
            alias = aliases.get(m, m)
            d.infos['manufacturer'] = alias
            manufacturers[alias].append(d)

        for m, ds in manufacturers.items():
            if m not in self._manufacturers:
                if removed:
                    continue
                self._manufacturers[m] = \
                    ManufacturerInfos(name=m, kind=self.kind,
                                      use_series=self.use_series)

            manufacturer = self._manufacturers[m]
            manufacturer.update_series_and_models(ds, removed)
            if (removed and
                    not manufacturer._series and not manufacturer._models):
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
        ms = [m for m in self._manufacturers.values() if m.instruments]
        ms.sort(key=attrgetter('name'))
        self.manufacturers = ms


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

    #: Dict of the connections
    connections = Dict()

    #: Dict of the settings
    settings = Dict()

    def write_to_file(self):
        """Save the profile to a file.

        """
        self._config.filename = self.path
        self._config.update(dict(id=self.id, model_id=self.model.id,
                                 connections=self.connections,
                                 settings=self.settings))
        self._config.write()

    def clone(self):
        """Clone this object.

        """
        c = ConfigObj(encoding='utf-8')
        c.update(dict(id=self.id, model_id=self.model.id,
                      connections=self.connections,
                      settings=self.settings))
        return type(self)(path=self.path, _config=c, plugin=self.plugin)

    @classmethod
    def create_blank(cls, plugin):
        """Create a new blank ProfileInfos.

        """
        c = ConfigObj(encoding='utf-8')
        c['id'] = ''
        c['model_id'] = ''
        c['connections'] = {}
        c['settings'] = {}
        return cls(plugin=plugin, _config=c)

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: ConfigObj object associated to the profile.
    _config = Value()

    def _default_id(self):
        """Get the id from the profile.

        """
        return self._config['id']

    def _default_model(self):
        """Get the model from the profile.

        """
        infos = self._config['model_id'].split('.')
        h = self.plugin._manufacturers
        if len(infos) == 2:
            manufacturer, model = infos
            return h._manufacturers[manufacturer]._models[model]
        if len(infos) == 3:
            manufacturer, serie, model = infos
            m = h._manufacturers[manufacturer]
            return m._series[serie]._models[model]

    def _default_connections(self):
        """Get the defined connections from the profile.

        """
        return dict(self._config['connections'])

    def _default_settings(self):
        """Get the defined settings from the profile.

        """
        return dict(self._config['settings'])

    def _default__config(self):
        """Load the config from the file.

        """
        return ConfigObj(self.path, encoding='utf-8')

    def _post_setattr__config(self, old, new):
        """Clean id, model, connections and settings so that default is called
        again.

        """
        del self.id, self.model, self.connections, self.settings


def validate_profile_infos(infos):
    """Make sure that a ProfileInfos is backed by a correct file.

    """
    for m in ('id', 'model', 'connections', 'settings'):
        try:
            delattr(infos, m)
            getattr(infos, m)
        except KeyError as e:
            msg = ('The profile stored in {} does not declare the {} field or'
                   ' it contains incorrect values : {}')
            return False, msg.format(infos.path, m, e)

    return True, ''
