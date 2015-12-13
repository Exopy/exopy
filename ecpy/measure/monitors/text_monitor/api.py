# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Text monitor API allowing to extend it through plugin contributions.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import enaml

from .rules.base import BaseRule, RuleType, RuleConfig
with enaml.imports():
    from .rules.base_views import BaseRuleView

__all__ = ['BaseRule', 'RuleType', 'RuleConfig', 'BaseRuleView']
