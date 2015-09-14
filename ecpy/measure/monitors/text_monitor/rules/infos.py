# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Container object to store rules declarations.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import enaml
from atom.api import Atom, Typed

from .base import BaseRule
with enaml.imports():
    from .base_views import BaseRuleView


class RuleInfos(Atom):
    """Container object to store rules declarations.

    """
    #: Class implementing the logic of the rule.
    cls = Typed(BaseRule)

    #: Enaml widget used to edit the rules parameters.
    view = Typed(BaseRuleView)
