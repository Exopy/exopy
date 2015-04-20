# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test state plugin system.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)
from enaml.workbench.api import Workbench
import enaml
from pytest import raises

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from ecpy.app.states.manifest import StateManifest
    from .states_utils import StateContributor


CORE_PLUGIN = 'enaml.workbench.core'
GET_STATE = 'ecpy.app.states.get'

STATE_ID = 'test.states.state'


class TestState(object):
    """Test the handling os states by the state plugin.

    """
    def setup(self):
        self.workbench = Workbench()
        self.workbench.register(CoreManifest())
        self.workbench.register(StateManifest())
        self.workbench.register(StateContributor())

    def test_get_state(self):
        """Test accessing to a state object through the command.

        """
        core = self.workbench.get_plugin(CORE_PLUGIN)
        par = {'state_id': STATE_ID}
        state = core.invoke_command(GET_STATE,
                                    par, trigger=self)

        assert hasattr(state, 'string')
        assert state.string == 'init'
        with raises(AttributeError):
            state.string = 1

        self.workbench.unregister('ecpy.app.states')

    def test_state_unicity(self):
        """Test that asking twice the same state return the same object.

        """
        core = self.workbench.get_plugin(CORE_PLUGIN)
        par = {'state_id': STATE_ID}
        state1 = core.invoke_command(GET_STATE,
                                     par, trigger=self)
        state2 = core.invoke_command(GET_STATE,
                                     par, trigger=self)
        assert state1 is state2

    def test_member_sync(self):
        """Test that the state is correctly synchronised with the plugin.

        """
        core = self.workbench.get_plugin(CORE_PLUGIN)
        par = {'state_id': STATE_ID}
        state = core.invoke_command(GET_STATE,
                                    par, trigger=self)

        plugin = self.workbench.get_plugin('test.states')
        plugin.string = 'test'

        assert state.string == 'test'

    def test_death_notif(self):
        """Test that a state whose plugin is unregistered is marked as dead.

        """
        core = self.workbench.get_plugin(CORE_PLUGIN)
        par = {'state_id': STATE_ID}
        state = core.invoke_command(GET_STATE,
                                    par, trigger=self)

        self.workbench.unregister(u'test.states')
        assert not state.alive
