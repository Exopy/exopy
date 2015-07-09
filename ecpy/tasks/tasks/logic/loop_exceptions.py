# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Exceptions used to interact with looping tasks.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)


class LoopException(BaseException):
    pass


class BreakException(LoopException):
    """Exception used to signal a looping task it should break.

    """
    pass


class ContinueException(LoopException):
    """Exception used to signal a looping task it should continue.

    """
    pass
