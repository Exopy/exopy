# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""ecpy.measure : Measure edition and execution

The measure plugin handles the edition and execution of a measure centered
on a task. A measure execution can be customized using hooks adding operations
before and after the main task, can be monitored also. The edition of the main
task is customizable.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)


def list_manifests():
    """List all the manifests to register at startup.

    """
    import enaml
    with enaml.imports():
        from .manifest import MeasureManifest
        from .monitors.text_monitor.manifest import TextMonitorManifest

    return [MeasureManifest, TextMonitorManifest]
