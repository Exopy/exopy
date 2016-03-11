# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2016 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Base class for task needing to access an instrument.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import (Tuple, Value)

from .base_tasks import SimpleTask


class InstrumentTask(SimpleTask):
    """Base class for all tasks calling instruments.

    """
    #: Selected instrument as (profile, driver, collection, settings) tuple
    selected_instrument = Tuple(default=('', '', '', '')).tag(pref=True)

    #: Instance of instrument driver.
    driver = Value()

    def check(self, *args, **kwargs):
        """Chech that the provided informations allows to establish the
        connection to the instrument.

        """
        err_path = self.path + '/' + self.name
        run_time = self.root_task.run_time
        traceback = {}
        profile = None

        if self.selected_instrument and len(self.selected_instrument) == 4:
            p_id, d_id, c_id, s_id = self.selected_instrument
            if 'profiles' in run_time:
                # Here use .get() to avoid errors if we were not granted the
                # use of the profile. In that case config won't be used.
                profile = run_time['profiles'].get(p_id)
        else:
            msg = ('No instrument was selected or not all informations were '
                   'provided. The instrument selected should be sepcified as '
                   '(profile_id, driver_id, connection_id, settings_id). '
                   'settings_id can be None')
            traceback[err_path] = msg
            return False, traceback

        if run_time and d_id in run_time['drivers']:
            d_cls, starter = run_time['drivers'][d_id]
        else:
            traceback[err_path] = 'Failed to get the specified instr driver.'
            return False, traceback

        if profile:
            if c_id not in profile['connections']:
                traceback[err_path] = ('The selected profile does not contain '
                                       'the %s connection') % c_id
                return False, traceback
            elif s_id is not None and s_id not in profile['settings']:
                traceback[err_path] = ('The selected profile does not contain '
                                       'the %s settings') % c_id
                return False, traceback

            if kwargs.get('test_instr'):
                res, msg = starter.check_infos(d_cls,
                                               profile['connections'][c_id],
                                               profile['settings'][s_id])
                if not res:
                    traceback[err_path] = msg
                    return False, traceback

        return True, traceback

    def start_driver(self):
        """Create an instance of the instrument driver and connect it.

        """
        run_time = self.root_task.run_time
        instrs = self.root_task.resources['instrs']
        p_id, d_id, c_id, s_id = self.selected_instrument
        if p_id in instrs:
            self.driver = instrs[p_id][0]
        else:
            profile = run_time['profiles'][p_id]
            d_cls, starter = run_time['drivers'][d_id]
            self.driver = starter.initialize(d_cls,
                                             profile['connections'][c_id],
                                             profile['settings'][s_id])
            instrs[p_id] = (self.driver, starter)
