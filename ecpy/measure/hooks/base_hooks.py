# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Base classes for all measure hooks.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from ..base_tool import BaseMeasureTool, BaseToolDeclaration


class BaseExecutionHook(BaseMeasureTool):
    """Base class for all measure hooks (pre or post execution).

    """

    def run(self, workbench, measure, **kwargs):
        """Perform additional operations before/after the measure.

        Parameters
        ----------
        workbench : Workbench
            Reference to the application workbench.

        measure : Measure
            Reference to the measure.

        **kwargs :
            Additional keywords arguments. Those can be falgs specifying what
            kind of operations can or cannot be perfomed.

        """
        raise NotImplementedError()


class BasePreExecutionHook(BaseExecutionHook):
    """Base class for pre-execution measure hooks.

    """
    pass


class BasePostExecutionHook(BaseExecutionHook):
    """Base class for post-execution measure hooks.

    """
    pass


class PreExecutionHook(BaseToolDeclaration):
    """A declarative class for contributing a measure pre-execution.

    PreExecutionHook object can be contributed as extensions child to the
    'pre-execution' extension point of the 'ecpy.measure' plugin.

    """
    pass


class PostExecutionHook(BaseToolDeclaration):
    """A declarative class for contributing a measure post-execution.

    PostExecutionHook object can be contributed as extensions child to the
    'post-execution' extension point of the 'ecpy.measure' plugin.

    """
    pass
