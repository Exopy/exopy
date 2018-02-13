# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""State plugin definition.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import contextlib
from atom.api import (Atom, Bool, Value, Typed, Dict)
from enaml.workbench.api import Plugin

from .state import State
from ...utils.plugin_tools import ExtensionsCollector


class _StateHolder(Atom):
    """Base class for all state holders of the state plugin.

    This base class is subclassed at runtime to create custom Atom object with
    the right members.

    """
    alive = Bool(True)

    _allow_set = Bool(False)

    def __setattr__(self, name, value):
        if self._allow_set or name == '_allow_set':
            super(_StateHolder, self).__setattr__(name, value)
        else:
            raise AttributeError('Attributes of states holder are read-only')

    @contextlib.contextmanager
    def setting_allowed(self):
        """Context manager to prevent users of the state to corrupt it

        """
        self._allow_set = True
        try:
            yield
        finally:
            self._allow_set = False

    def updater(self, changes):
        """Observer handler keeping the state up to date with the plugin.

        """
        with self.setting_allowed():
            setattr(self, changes['name'], changes['value'])


STATE_POINT = 'exopy.app.states.state'


class StatePlugin(Plugin):
    """A plugin to manage application wide available states.

    """

    def start(self):
        """Start the plugin life-cycle.

        """
        def _validate(state):
            msg = 'State does not declare any sync members.'
            return bool(state.sync_members), msg

        self._states = ExtensionsCollector(workbench=self.workbench,
                                           point=STATE_POINT,
                                           ext_class=State,
                                           validate_ext=_validate)

        self._states.observe('contributions', self._notify_states_death)
        self._states.start()

    def stop(self):
        """ Stop the plugin life-cycle.

        This method is called by the framework at the appropriate time.
        It should never be called by user code.

        """
        self._states.unobserve('contributions', self._notify_states_death)
        self._states.stop()

    def get_state(self, state_id):
        """Return the state associated to the given id.

        """
        if state_id not in self._living_states:
            state_obj = self._build_state(state_id)
            self._living_states[state_id] = state_obj

        return self._living_states[state_id]

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: ExtensionsCollector keeping track of the declared states.
    _states = Typed(ExtensionsCollector)

    #: Dictionary keeping track of created and live states objects.
    _living_states = Dict()

    def _build_state(self, state_id):
        """Create a custom _StateHolder class at runtime and instantiate it.

        Parameters
        ----------
        state_id : unicode
            Id of the state to return.

        Returns
        -------
        state : _StateHolder
            State reflecting the sync_members of the plugin to which it is
            linked.

        """
        state = self._states.contributions[state_id]

        # Explicit casting required as Python 2 does not like Unicode for class
        # name
        class_name = str(''.join([s.capitalize()
                                  for s in state_id.split('.')]))

        members = {}
        # Explicit casting required as Python 2 does not like Unicode for
        # members name
        for m in state.sync_members:
            members[str(m)] = Value()
        state_class = type(class_name, (_StateHolder,), members)

        # Instantiation , initialisation, and binding of the state object to
        # the plugin declaring it.
        state_object = state_class()
        extension = self._states.contributed_by(state_id)
        plugin = self.workbench.get_plugin(extension.plugin_id)
        with state_object.setting_allowed():
            for m in state.sync_members:
                setattr(state_object, m, getattr(plugin, m))
            plugin.observe(m, state_object.updater)

        return state_object

    def _notify_states_death(self, change):
        """Notify that the plugin contributing a state is not plugged anymore.

        This method is used to observe the contribution member of the _states.

        """
        if 'oldvalue' in change:
            deads = set(change['oldvalue']) - set(change['value'])
            for dead in deads:
                if dead in self._living_states:
                    state = self._living_states[dead]
                    with state.setting_allowed():
                        state.alive = False
                    del self._living_states[dead]
