# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Base class for tasks needing to access an instrument.

"""
from contextlib import contextmanager

from atom.api import (Tuple, Value, Dict)

from .base_tasks import SimpleTask

from ...utils.atom_util import tagged_members


PROFILE_DEPENDENCY_ID = 'exopy.instruments.profiles'

DRIVER_DEPENDENCY_ID = 'exopy.instruments.drivers'


class InstrumentTask(SimpleTask):
    """Base class for all tasks calling instruments.

    """
    #: Selected instrument as (profile, driver, collection, settings) tuple
    selected_instrument = Tuple(default=('', '', '', '')).tag(pref=True)

    #: Instance of instrument driver.
    driver = Value()

    # HINT done this way so that classes overriding this one does not
    # forget to preserve it.
    def __init__(self, **kwargs):
        super(InstrumentTask, self).__init__(**kwargs)
        de = self.database_entries.copy()
        de['instrument'] = ''
        self.database_entries = de

    def check(self, *args, **kwargs):
        """Chech that the provided informations allows to establish the
        connection to the instrument.

        """
        # TODO add a check that the same profile is not used by different tasks
        # with different infos (need a way to share states, could use the
        # errors member of the root or similar, to avoid modifying the way
        # this method is called.
        test, traceback = super(InstrumentTask, self).check(*args, **kwargs)
        err_path = self.get_error_path() + '-instrument'
        run_time = self.root.run_time
        profile = None

        if self.selected_instrument and len(self.selected_instrument) == 4:
            p_id, d_id, c_id, s_id = self.selected_instrument
            self.write_in_database('instrument', p_id)
            # Here use .get() to avoid errors if we were not granted the
            # use of the profile. In that case config won't be used.
            # Note that the Measurement guarantees that all requested runtime
            # dependencies section will be present even if they are empty,
            # which makes it safe to access PROFILE_DEPENDENCY_ID
            profile = run_time[PROFILE_DEPENDENCY_ID].get(p_id)
        else:
            msg = ('No instrument was selected or not all informations were '
                   'provided. The instrument selected should be specified as '
                   '(profile_id, driver_id, connection_id, settings_id). '
                   'settings_id can be None')
            traceback[err_path] = msg
            return False, traceback

        if run_time and d_id in run_time[DRIVER_DEPENDENCY_ID]:
            d_cls, starter = run_time[DRIVER_DEPENDENCY_ID][d_id]
        else:
            msg = ('Failed to get the specified driver : %s. Collected drivers'
                   ' are %s.')
            traceback[err_path] = msg % (d_id, run_time[DRIVER_DEPENDENCY_ID])
            return False, traceback

        if profile:
            if c_id not in profile['connections']:
                traceback[err_path] = ('The selected profile does not contain '
                                       'the %s connection') % c_id
                return False, traceback
            elif s_id is not None and s_id not in profile['settings']:
                traceback[err_path] = ('The selected profile does not contain '
                                       'the %s settings') % s_id
                return False, traceback

            if kwargs.get('test_instr', True):
                s = profile['settings'].get(s_id, {})
                res, msg = starter.check_infos(d_cls,
                                               profile['connections'][c_id], s
                                               )
                if not res:
                    traceback[err_path] = msg
                    return False, traceback

        return test, traceback

    def prepare(self):
        """Always start the driver.

        """
        super(InstrumentTask, self).prepare()
        self.write_in_database('instrument', self.selected_instrument[0])
        self.start_driver()

    def start_driver(self):
        """Create an instance of the instrument driver and connect it.

        """
        run_time = self.root.run_time
        instrs = self.root.resources['instrs']
        p_id, d_id, c_id, s_id = self.selected_instrument
        if self.selected_instrument in instrs:
            self.driver = instrs[self.selected_instrument][0]
        else:
            profile = run_time[PROFILE_DEPENDENCY_ID][p_id]
            d_cls, starter = run_time[DRIVER_DEPENDENCY_ID][d_id]
            # Profile do not always contain a settings.
            self.driver = starter.start(d_cls,
                                        profile['connections'][c_id],
                                        profile['settings'].get(s_id, {}))
            # HINT allow something dangerous as the same instrument can be
            # accessed using multiple settings.
            # User should be careful about this (and should be warned)
            instrs[self.selected_instrument] = (self.driver, starter)

    @contextmanager
    def test_driver(self):
        """Safe temporary access to the driver to run some checks.

        Yield either a fully initialized driver or None.

        """
        try:
            run_time = self.root.run_time
            p_id, d_id, c_id, s_id = self.selected_instrument
            profile = run_time[PROFILE_DEPENDENCY_ID][p_id]
            d_cls, starter = run_time[DRIVER_DEPENDENCY_ID][d_id]
            driver = starter.start(d_cls,
                                   profile['connections'][c_id],
                                   profile['settings'][s_id])
        except Exception:
            driver = None

        yield driver

        if driver:
            starter.stop(driver)


class MultiInstrumentTask(SimpleTask):
    """Base class for all tasks calling multiple instruments.

    """
    #: Instance of multiple instrument drivers.
    drivers = Dict()

#        val = getattr(self, name)
#        self.preferences[name] = member_to_pref(self, member, val)
    # HINT done this way so that classes overriding this one does not
    # forget to preserve it.
    def __init__(self, **kwargs):
        super(MultiInstrumentTask, self).__init__(**kwargs)
        de = self.database_entries.copy()
        de['instrument'] = ''
        self.database_entries = de

    def check(self, *args, **kwargs):
        """Chech that the provided informations allows to establish the
        connection to the instrument.

        """
        # TODO add a check that the same profile is not used by different tasks
        # with different infos (need a way to share states, could use the
        # errors member of the root or similar, to avoid modifying the way
        # this method is called.
        for name, member in tagged_members(self, 'instr').items():
            print(name)
            print(member)
        test, traceback = super(MultiInstrumentTask, self).check(*args,
                                                                 **kwargs)
#        err_path = self.get_error_path() + '-instrument'
#        run_time = self.root.run_time
#        profile = None
#
#        if self.selected_instrument and len(self.selected_instrument) == 4:
#            p_id, d_id, c_id, s_id = self.selected_instrument
#            self.write_in_database('instrument', p_id)
#            if PROFILE_DEPENDENCY_ID in run_time:
#                # Here use .get() to avoid errors if we were not granted the
#                # use of the profile. In that case config won't be used.
#                profile = run_time[PROFILE_DEPENDENCY_ID].get(p_id)
#        else:
#            msg = ('No instrument was selected or not all informations were '
#                   'provided. The instrument selected should be specified as '
#                   '(profile_id, driver_id, connection_id, settings_id). '
#                   'settings_id can be None')
#            traceback[err_path] = msg
#            return False, traceback
#
#        if run_time and d_id in run_time[DRIVER_DEPENDENCY_ID]:
#            d_cls, starter = run_time[DRIVER_DEPENDENCY_ID][d_id]
#        else:
#            msg = ('Failed to get the specified driver : %s. Collected drivers'
#                   ' are %s.')
#            traceback[err_path] = msg % (d_id, run_time[DRIVER_DEPENDENCY_ID])
#            return False, traceback
#
#        if profile:
#            if c_id not in profile['connections']:
#                traceback[err_path] = ('The selected profile does not contain '
#                                       'the %s connection') % c_id
#                return False, traceback
#            elif s_id is not None and s_id not in profile['settings']:
#                traceback[err_path] = ('The selected profile does not contain '
#                                       'the %s settings') % s_id
#                return False, traceback
#
#            if kwargs.get('test_instr', True):
#                s = profile['settings'].get(s_id, {})
#                res, msg = starter.check_infos(d_cls,
#                                               profile['connections'][c_id], s
#                                               )
#                if not res:
#                    traceback[err_path] = msg
#                    return False, traceback

        return test, traceback

    def prepare(self):
        """Always start the driver.

        """
        super(MultiInstrumentTask, self).prepare()
        self.write_in_database('instrument', self.selected_instrument[0])
        #self.start_driver()

    def start_driver(self):
        """Create an instance of the instrument driver and connect it.

        """
        a = 1
#        run_time = self.root.run_time
#        instrs = self.root.resources['instrs']
#        p_id, d_id, c_id, s_id = self.selected_instrument
#        if self.selected_instrument in instrs:
#            self.drivers[''] = instrs[self.selected_instrument][0]
#        else:
#            profile = run_time[PROFILE_DEPENDENCY_ID][p_id]
#            d_cls, starter = run_time[DRIVER_DEPENDENCY_ID][d_id]
#            # Profile do not always contain a settings.
#            self.driver = starter.start(d_cls,
#                                        profile['connections'][c_id],
#                                        profile['settings'].get(s_id, {}))
#            # HINT allow something dangerous as the same instrument can be
#            # accessed using multiple settings.
#            # User should be careful about this (and should be warned)
#            instrs[self.selected_instrument] = (self.driver, starter)

    @contextmanager
    def test_driver(self):
        """Safe temporary access to the driver to run some checks.

        Yield either a fully initialized driver or None.

        """
        b = 1
#        try:
#            run_time = self.root.run_time
#            p_id, d_id, c_id, s_id = self.selected_instrument
#            profile = run_time[PROFILE_DEPENDENCY_ID][p_id]
#            d_cls, starter = run_time[DRIVER_DEPENDENCY_ID][d_id]
#            driver = starter.start(d_cls,
#                                   profile['connections'][c_id],
#                                   profile['settings'][s_id])
#        except Exception:
#            driver = None
#
#        yield driver
#
#        if driver:
#            starter.stop(driver)
