# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""exopy.measurement : Measurement edition and execution

The measurement plugin handles the edition and execution of a measurement
centered on a task. A measurement execution can be customized using hooks
adding operations before and after the main task, can be monitored also. The
edition of the main task is customizable.

"""


def list_manifests():
    """List all the manifests to register at startup.

    """
    import enaml
    with enaml.imports():
        from .manifest import MeasurementManifest
        from .monitors.text_monitor.manifest import TextMonitorManifest

    return [MeasurementManifest, TextMonitorManifest]
