# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Plugin managing the preferences of the TextMonitor such as rules.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import logging
from atom.api import List, Dict, Typed

from ....utils.has_pref_plugin import HasPrefPlugin
from ....utils.plugin_tools import (DeclaratorsCollector, ExtensionsCollector,
                                    make_extension_validator)
from ..base_monitor import Monitor
from .monitor import TextMonitor
from .rules.base import RuleType, Rules, RuleConfig


RULE_TYPE_POINT = 'ecpy.measure.monitors.text_monitor.rule_type'

RULE_CONFIG_POINT = 'ecpy.measure.monitors.text_monitor.rule_config'

logger = logging.getLogger(__name__)


class TextMonitorPlugin(HasPrefPlugin):
    """Plugin managing the preferences of the TextMonitor.

    """

    # List of rules which should be created automatically for new monitors.
    default_rules = List().tag(pref=True)

    # List of available rule types.
    rule_types = List()

    # List of available rules configurations.
    rules = List()

    def start(self):
        """Start the plugin life-cycle.

        """
        super(TextMonitorPlugin, self).start()
        self._rule_types = DeclaratorsCollector(workbench=self.workbench,
                                                point=RULE_TYPE_POINT,
                                                ext_class=(Rules, RuleType))
        self._rules_types.start()

        validator = make_extension_validator(RuleConfig,
                                             attributes=('id', 'description',
                                                         'rule_type', 'config')
                                             )
        self._rule_configs = ExtensionsCollector(workbench=self.workbench,
                                                 point=RULE_CONFIG_POINT,
                                                 ext_class=RuleConfig,
                                                 valiadtor=validator)
        self._rule_configs.start()

        # List all the rule types and rules and remove unknown rules from
        # the default ones.
        self._update_rule_types()
        self._update_rules()
        defaults = [r for r in self.default_rules if r in self.rules]
        if defaults != self.default_rules:
            msg = ('The following rules for the TextMonitor are not defined, '
                   'and have been removed from the defaults : %s')
            removed = set(self.default_rules) - set(defaults)
            logger.warning(msg, removed)
            self.default_rules = defaults

        self._bind_observers()

    def stop(self):
        """Stop the plugin and clear all ressources.

        """
        self._unbind_observers()

        self.rule_types = []
        self.rules = []
        self._rule_types.stop()
        self._rule_configs.stop

    def build_rule(self, name_or_config):
        """ Build rule from a dict.

        Parameters
        ----------
        name_or_config : unicode|dict
            Name of the rule to build or dict containing the infos to build the
            rule from scratch.

        Returns
        -------
        rule : BaseRule|None
            New rule properly initialized.

        """
        if not isinstance(name_or_config, dict):
            if name_or_config in self._user_rules:
                config = self._user_rules[name_or_config].copy()
            elif name_or_config in self._rule_configs:
                rule_config = self._rule_configs[name_or_config]
                config = rule_config.configs.copy()
                config['class_id'] = rule_config.rule_type
            else:
                msg = 'Requested rule not found : {}'.format(name_or_config)
                logger.warn(msg)
                return

        else:
            config = name_or_config

        class_id = config.pop('class_id')
        rule_class = self._rule_types.contributions.get(class_id)
        if rule_class is not None:
            rule = rule_class()
            rule.update_members_from_preferences(**config)
            return rule

        else:
            msg = 'Requested rule class not found : {}'.format(class_id)
            logger.warn(msg)

    def get_rule_type(self, rule_type_id):
        """Access the class corresponding to a given id.

        """
        return self._rule_types.contributions[rule_type_id].cls

    def get_rule_view(self, rule):
        """CReate a view corresponding to the given object.

        """
        return self._rule_types.contributions[rule].view(rule=rule,
                                                         plugin=self)

    def save_rule(self, rule):
        """Add a rule present on a plugin to the saved rules.

        """
        self._user_rules[rule.id] = rule.preferences_from_members()

    def create_monitor(self, default=False):
        """ Create a new monitor.

        Parameters
        ----------
        default : bool, optionnal
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

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Collect the rule types contributions.
    _rule_types = Typed(DeclaratorsCollector)

    #: Collect the rule config declarations and use them to update the config
    _rule_configs = Typed(ExtensionsCollector)

    #: User defined rules config saved in the preferences.
    _user_rules = Dict().tag(pref=True)

    def _update_rule_types(self, change):
        """Update the public rule types class id when new ones get registered.

        """
        self.rule_types = list(self._rule_types.contributions)

    def _update_rules(self, change):
        """Update the rule names whenever a new contributed rule or a new user
        rule is added.

        """
        contrib = set(self._rule_configs.contributions)
        users = set(self._user_rules)
        self.rules = list(contrib + users)

    def _bind_observers(self):
        """Observe the collectors to update public attributes.

        """
        self._rule_configs.observe('contributions', self._update_rules)
        self._rule_types.observe('contributions', self._update_rule_types)

    def _unbind_observers(self):
        """Unobserve the collectors.

        """
        self._rule_configs.unobserve('contributions', self._update_rules)
        self._rule_types.unobserve('contributions', self._update_rule_types)
