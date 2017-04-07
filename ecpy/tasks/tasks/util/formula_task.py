# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Task for defining mathematical formulas.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from collections import OrderedDict

from atom.api import (Typed, set_default)

from ....utils.traceback import format_exc
from ....utils.atom_util import (ordered_dict_from_pref, ordered_dict_to_pref)

from ..base_tasks import SimpleTask


class FormulaTask(SimpleTask):
    """Compute values according to formulas.

    Any valid python expression can be evaluated; any valid key entry of the
    database will be replaced by it's value.

    """
    #: List of formulas.
    #: To modify it (add/remove entry) the dictionary must be copied, modified
    #: and then reassigned.
    formulas = Typed(OrderedDict, ()).tag(pref=[ordered_dict_to_pref,
                                                ordered_dict_from_pref])

    wait = set_default({'activated': True})  # Wait on all pools by default.

    def perform(self):
        """Evaluate alll formulas and update the database.

        """
        for k, v in self.formulas.items():
            value = self.format_and_eval_string(v)
            self.write_in_database(k, value)

    def check(self, *args, **kwargs):
        """Validate that all formulas can be evaluated.

        """
        traceback = {}
        test = True
        err_path = self.get_error_path()
        for k, v in self.formulas.items():
            try:
                value = self.format_and_eval_string(v)
                self.write_in_database(k, value)
            except Exception:
                test = False
                name = err_path + '-' + k
                traceback[name] =\
                    "Failed to eval the formula {}: {}".format(k, format_exc())
        return test, traceback

    def _post_setattr_formulas(self, old, new):
        """Observer keeping the database entries in sync with the declared
        formulas.

        """
        self.database_entries = {key: 1.0 for key in new}
