# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Container object to store rules declarations.

"""
import enaml
from atom.api import Atom, Subclass

from .base import BaseRule
with enaml.imports():
    from .base_views import BaseRuleView


class RuleInfos(Atom):
    """Container object to store rules declarations.

    """
    #: Class implementing the logic of the rule.
    cls = Subclass(BaseRule)

    #: Enaml widget used to edit the rules parameters.
    view = Subclass(BaseRuleView)
