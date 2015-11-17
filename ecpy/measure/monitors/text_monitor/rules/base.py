# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Rules allow to defines some automatic handling of database entries in the
TextMonitor.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from inspect import cleandoc
from traceback import format_exc

from future.utils import python_2_unicode_compatible
from atom.api import Unicode, List, Dict
from enaml.core.api import Declarative, d_

from .....utils.atom_util import HasPrefAtom
from .....utils.declarator import (Declarator, GroupDeclarator,
                                   import_and_get)


class BaseRule(HasPrefAtom):
    """Base class for all rules implementations.

    """
    #: Name of the rule.
    id = Unicode().tag(pref=True)

    #: Quick description of what this rule is intended for.
    description = d_(Unicode()).tag(pref=True)

    #: List of database entries suffixes used to identify the entries which
    #: contributes to the rule.
    suffixes = List(default=['']).tag(pref=True)

    #: Id of the class used for persistence.
    class_id = Unicode().tag(pref=True)

    def try_apply(self, new_entry, monitor):
        """ Attempt to apply the rule.

        Parameters
        ----------
        new_entry : str
            Database path of the newly added entry.

        monitor : TextMonitor
            Instance of the text monitor trying to apply the rule.

        """
        raise NotImplementedError()

    def _default_class_id(self):
        """Default factory for the class_id attribute

        """
        pack, _ = self.__module__.split('.', 1)
        return '.'.join((pack, type(self).__name__))


class Rules(GroupDeclarator):
    """Declarator used to group rules declarations.

    """
    pass


@python_2_unicode_compatible
class RuleType(Declarator):
    """Declarator used to contribute a text monitor rule.

    """
    #: Path to the rule object. Path should be dot separated and the class
    #: name preceded by ':'.
    #: ex: ecpy.measure.monitors.text_monitor.std_rules:RejectRule
    #: The path of any parent GroupDeclarator object will be prepended to it.
    rule = d_(Unicode())

    #: Path to the view object associated with the task.
    #: The path of any parent GroupDeclarator object will be prepended to it.
    view = d_(Unicode())

    def register(self, collector, traceback):
        """Collect rule and view and store them into the DeclaratorCollector
        contributions member.

        The group declared by a parent if any is taken into account.

        """
        # Determine the path to the task and view.
        path = self.get_path()
        try:
            r_path, rule = (path + '.' + self.rule
                            if path else self.rule).split(':')
            v_path, view = (path + '.' + self.view
                            if path else self.view).split(':')
        except ValueError:
            msg = 'Incorrect %s (%s), path must be of the form a.b.c:Class'
            if ':' in self.rule:
                err_id = r_path.split('.', 1)[0] + '.' + rule
                msg = msg % ('view', self.view)
            else:
                err_id = 'Error %d' % len(traceback)
                msg = msg % ('task', self.rule)

            traceback[err_id] = msg
            return

        # Build the rule id by assembling the package name and the class name
        rule_id = r_path.split('.', 1)[0] + '.' + rule

        # Check that the rule does not already exist.
        if rule_id in collector.contributions or rule_id in traceback:
            i = 1
            while True:
                err_id = '%s_duplicate%d' % (rule_id, i)
                if err_id not in traceback:
                    break

            msg = 'Duplicate definition of {}, found in {}'
            traceback[err_id] = msg.format(rule, r_path)
            return

        from .infos import RuleInfos
        r_infos = RuleInfos()

        # Get the rule class.
        rule_cls = import_and_get(r_path, rule, traceback, rule_id)
        if rule_cls is None:
            return

        try:
            r_infos.cls = rule_cls
        except TypeError:
            msg = '{} should a subclass of BaseRule.\n{}'
            traceback[rule_id] = msg.format(rule_cls, format_exc())
            return

        # Get the rule view.
        rule_view = import_and_get(v_path, view, traceback, rule_id)
        if rule_view is None:
            return

        try:
            r_infos.view = rule_view
        except TypeError:
            msg = '{} should a subclass of BaseRuleView.\n{}'
            traceback[rule_id] = msg.format(rule_view, format_exc())
            return

        collector.contributions[rule_id] = r_infos

        self.is_registered = True

    def unregister(self, collector):
        """Remove contributed infos from the collector.

        """
        if self.is_registered:
            # Remove infos.
            rule = self.rule.split(':')[1]
            try:
                del collector.contributions[rule]
            except KeyError:
                pass

            self.is_registered = False

    def __str__(self):
        """Nice string representation giving attributes values.

        """
        msg = cleandoc('''{} with:
                       rule: {}, view : {}''')
        pack, _ = self.__module__.__name__.split('.', 1)
        return msg.format(pack + '.' + type(self).__name__,
                          self.rule, self.view)


class RuleConfig(Declarative):
    """Object to contribute a concrete rule.

    This rule will only be used if no user defined rule with the same name
    is defined.

    """
    #: Id of this rule configuration this should be unique.
    id = d_(Unicode())

    #: Quick description of what this rule is intended for.
    description = d_(Unicode())

    #: Id of the rule to use. This is dot separated string containing the
    #: name of the package defining the rule type and the rule type name.
    rule_type = d_(Unicode())

    #: Configuration dictionary to use to instantiate the rule
    config = d_(Dict())
