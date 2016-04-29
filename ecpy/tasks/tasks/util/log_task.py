# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Logging Task.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import (Unicode, set_default)
import logging

from ..base_tasks import SimpleTask


class LogTask(SimpleTask):
    """ Task logging a message. Loopable.

    """

    #: Class attribute marking this task as being logical, used in filtering.
    util_task = True

    #: Message to log when the task is executed.
    message = Unicode().tag(pref=True, fmt=True)

    loopable = True
    database_entries = set_default({'message': ''})

    wait = set_default({'activated': True})  # Wait on all pools by default.

    def perform(self, *args, **kwargs):
        """ Format the message and log it.

        """
        mess = self.format_string(self.message)
        self.write_in_database('message', mess)
        logging.info(mess)
        return True
