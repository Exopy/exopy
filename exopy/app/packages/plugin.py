# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Plugin handling the collection and registering of extension packages.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pkg_resources
import logging

from atom.api import List, Dict
from enaml.workbench.api import Plugin, PluginManifest

from ...utils.traceback import format_exc

logger = logging.getLogger(__name__)


class PackagesPlugin(Plugin):
    """Plugin collecting and registering all manifest contributed by extension
    packages.

    """
    #: Dictionary listing the extension packages registered at startup, each
    #: entries can contain either a dict listing the id of the registered
    #: manifest with a message indicating whether registering succeeded, or
    #: a message explaining why the package was not loaded.
    packages = Dict()

    def stop(self):
        """Unregister all manifest contributed by extension packages.

        """
        # Sort to respect the given priority when unregistering.
        heap = sorted(self._registered)
        for manifest_id in heap:
            self.workbench.unregister(manifest_id[2])

        self.packages.clear()
        self._registered = []

    def collect_and_register(self):
        """Iter over packages and register the manifest they are providing.

        """
        # Getting core plugin to signal errors.
        core = self.workbench.get_plugin('enaml.workbench.core')
        cmd = 'exopy.app.errors.signal'

        packages = dict()
        registered = []
        core.invoke_command('exopy.app.errors.enter_error_gathering', {})
        for ep in pkg_resources.iter_entry_points('exopy_package_extension'):

            # Check that all dependencies are satisfied.
            try:
                ep.require()
            except Exception:
                msg = 'Could not load extension package %s : %s'
                msg = msg % (ep.name, format_exc())
                packages[ep.name] = msg
                core.invoke_command(cmd, dict(kind='package', id=ep.name,
                                              message=msg))
                continue

            # Get all manifests
            packages[ep.name] = {}
            manifests = ep.load()()
            if not isinstance(manifests, list):
                msg = 'Package %s entry point must return a list, not %s'
                msg = msg % (ep.name, str(type(manifests)))
                packages[ep.name] = msg
                core.invoke_command(cmd, dict(kind='package', id=ep.name,
                                              message=msg))
                continue

            if any(not issubclass(m, PluginManifest) for m in manifests):
                msg = 'Package %s entry point must only return PluginManifests'
                msg = msg % ep.name
                packages[ep.name] = msg
                core.invoke_command(cmd, dict(kind='package', id=ep.name,
                                              message=msg))
                continue

            for manifest in manifests:
                inst = manifest()
                try:
                    self.workbench.register(inst)
                except ValueError:
                    core.invoke_command(cmd,
                                        dict(kind='registering', id=inst.id,
                                             message=format_exc()))
                    continue

                packages[ep.name][inst.id] = 'Successfully registered'
                priority = getattr(inst, 'priority', 100)
                # Keep the insertion index, to avoid comparing id when
                # sorting (it would make no sense).
                registered.append((priority, len(registered), inst.id))

        self.packages = packages
        self._registered = registered
        core.invoke_command('exopy.app.errors.exit_error_gathering', {})

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Private list of registered manifest used when stopping the plugin.
    _registered = List()
