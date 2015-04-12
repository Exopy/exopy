# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Definition of the base tasks.

The base tasks define how task interact between them and with the database, how
ressources can be shared and how preferences are handled.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from textwrap import fill
from inspect import cleandoc
from math import (cos, sin, tan, acos, asin, atan, sqrt, log10,
                exp, log, cosh, sinh, tanh, atan2)
from cmath import pi as Pi
import numpy as np
import cmath as cm

FORMATTER_TOOLTIP = fill(cleandoc("""In this field you can enter a text and
                        include fields which will be replaced by database
                        entries by using the delimiters '{' and '}'."""), 80)

EVALUATER_TOOLTIP = '\n'.join([
    fill(cleandoc("""In this field you can enter a text and
                  include fields which will be replaced by database
                  entries by using the delimiters '{' and '}' and
                  which will then be evaluated."""), 80),
    "Available math functions:",
    "- cos, sin, tan, acos, asin, atan, atan2",
    "- exp, log, log10, cosh, sinh, tanh, sqrt",
    "- complex math function are available under cm",
    "- numpy function are avilable under np",
    "- pi is available as Pi"])


def safe_eval(expr, local_var=None):
    """Eval expr save is expr contains only letters.

    """
    if expr.isalpha():
        return expr

    if local_var:
        return eval(expr, globals(), local_var)
    else:
        return eval(expr)
