# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task for defining various definitions.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from collections import OrderedDict
from traceback import format_exc

from atom.api import Typed

from ....utils.atom_util import (ordered_dict_from_pref, ordered_dict_to_pref)
from ...tools.string_evaluation import safe_eval

from ...base_tasks import SimpleTask


class DefinitionTask(SimpleTask):
    """Task defining a list of global variables in the database. Possibly used
    in other tasks.

    Any valid python expression can be evaluated; any valid key entry of the
    database will be replaced by it's value.

    """
    #: Class attribute marking this task as being logical, used in filtering.
    util_task = True

    # Dictionary of definitions
    definitions = Typed(OrderedDict, ()).tag(pref=[ordered_dict_to_pref,
                                                   ordered_dict_from_pref])

    def perform(self):
        """ Do nothing (Declared only to avoid raising a NotImplementedError)

        """

    def check(self, *args, **kwargs):
        """ In the check() method we write all values to the database.

        """
        traceback = {}
        test = True
        for k, v in self.definitions.items():
            try:
                value = safe_eval(v, {})
                self.write_in_database(k, value)
            except Exception:
                test = False
                name = self.path + '/' + self.name + '-' + k
                traceback[name] =\
                    "Failed to eval the definition {}: {}".format(k,
                                                                  format_exc())
        return test, traceback

    def _post_setattr_definitions(self, old, new):
        """Observer keeping the database entries in sync with the declared
        definitions.

        """
        self.database_entries = {key: 1.0 for key in new}
