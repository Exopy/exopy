# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
# XXXX
"""

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import logging
from atom.api import List, Dict

from hqc_meas.utils.has_pref_plugin import HasPrefPlugin
from ..base_monitor import Monitor
from .monitor import TextMonitor


class TextMonitorPlugin(HasPrefPlugin):
    # XXXX
    """
    """

    # List of rules which should be created automatically for new monitors.
    default_rules = List().tag(pref=True)

    # XXXX make this extendible
    # Mapping between rules class names and rule classes.
    rules_classes = Dict()

    # XXXX make this extensible
    # Dict holding the infos necessary to rebuild rules on demand.
    rules = Dict().tag(pref=True)

    # XXXX
    def start(self):
        """
        """
        pass

    # XXXX
    def stop(self):
        """
        """
        pass

    def build_rule(self, rule_config):
        """ Build rule from a dict.

        Parameters
        ----------
        rule_config : dict
            Dict containing the infos to build the rule from scratch.

        Returns
        -------
        rule : AbstractMonitorRule
            New rule properly initialized.

        """
        class_name = rule_config.pop('class_name')
        rule_class = self.rules_classes.get(class_name)
        if rule_class is not None:
            rule = rule_class()
            rule.update_members_from_preferences(**rule_config)

            return rule

        else:
            logger = logging.getLogger(__name__)
            mess = 'Requested rule class not found : {}'.format(class_name)
            logger.warn(mess)

    def create_monitor(self, default=False):
        """ Create a new monitor.

        Parameters
        ----------
        raw : bool, optionnal
            Whether or not to add the default rules to the new monitor.

        Returns
        -------
        monitor : TextMonitor
            New text monitor.

        """
        exts = [e for e in self.manifest.extensions if e.id == 'monitors']
        decl = exts[0].get_child(Monitor)
        monitor = TextMonitor(_plugin=self,
                              declaration=decl)

        if not default:
            rules = []
            for rule_name in self.default_rules:
                config = self.rules.get(rule_name).copy()
                if config is not None:
                    rule = self.build_rule(config)
                    rules.append(rule)
                else:
                    logger = logging.getLogger(__name__)
                    mess = 'Requested rule not found : {}'.format(rule_name)
                    logger.warn(mess)

            monitor.rules = rules

        return monitor
