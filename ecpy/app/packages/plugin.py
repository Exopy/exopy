# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
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
from traceback import format_exc
from atom.api import List, Dict
from enaml.workbench.api import Plugin, PluginManifest


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

    # XXXX refactor to use errors plugin.
    def collect_and_register(self):
        """Iter over packages and register the manifest they are providing.

        """
        packages = dict()
        registered = []
        for ep in pkg_resources.iter_entry_points('ecpy_package_extension'):

            # Check that all dependencies are satisfied.
            try:
                ep.require()
            except Exception:
                msg = 'Could not load extension package %s : %s'
                msg = msg % (ep.name, format_exc())
                packages[ep.name] = msg
                logger.warn(msg)
                continue

            # Get all manifests
            packages[ep.name] = {}
            manifests = ep.load()()
            if not isinstance(manifests, list):
                msg = 'Package %s entry point must return a list, not %s'
                msg = msg % (ep.name, str(type(manifests)))
                packages[ep.name] = msg
                logger.warn(msg)
                continue

            if any(not issubclass(m, PluginManifest) for m in manifests):
                msg = 'Package %s entry point must only return PluginManifests'
                msg = msg % ep.name
                packages[ep.name] = msg
                logger.warn(msg)
                continue

            for manifest in manifests:
                inst = manifest()
                try:
                    self.workbench.register(inst)
                except ValueError:
                    logger.warn(format_exc())
                    continue

                packages[ep.name][inst.id] = 'Successfully registered'
                priority = getattr(inst, 'priority', 100)
                # Keep the insertion index, to avoid comparing id when
                # sorting (it would make no sense).
                registered.append((priority, len(registered), inst.id))

        self.packages = packages
        self._registered = registered

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Private list of registered manifest used when stopping the plugin.
    _registered = List()
