# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Definition of the base tasks.

The base tasks define how task interact between them and with the database, how
ressources can be shared and how preferences are handled.

"""
from textwrap import fill
from inspect import cleandoc
from math import (cos, sin, tan, acos, asin, atan, sqrt, log10,
                  exp, log, cosh, sinh, tanh, atan2)
from cmath import pi as Pi
import cmath as cm

try:
    import numpy as np
    NP_TIP = ["- numpy function are available under np"]
except ImportError:  # pragma: no cover
    NP_TIP = []  # pragma: no cover

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
    "- pi is available as Pi"] + NP_TIP)


def safe_eval(expr, local_var):
    """Eval expr with the given local variables.

    """
    return eval(expr, globals(), local_var)
