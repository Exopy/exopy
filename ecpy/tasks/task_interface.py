# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Definition of the base classes for interfaces in tasks.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from traceback import format_exc
from atom.api import Atom, ForwardTyped, Instance, Unicode, Dict

from ..utils.atom_util import HasPrefAtom, tagged_members
from .base_tasks import BaseTask


class InterfaceableTaskMixin(Atom):
    """Mixin class for defining a task using interfaces.

    When defining a new interfaceablke task this mixin should always be the
    letf most class when defining the inheritance. This is due to the Python
    Method Resolution Order (mro) and the fact that this mixin must override
    methods defined in tasks.
    ex : MyTaskI(InterfaceableTaskMixin, MyTask):

    InterfaceableTaskMixin must appear a single time in the mro. This is
    checked by the manager at loading time.


    """
    #: A reference to the current interface for the task.
    interface = ForwardTyped(lambda: TaskInterface)

    def check(self, *args, **kwargs):
        """ Check the interface.

        This run the checks of the next parent class in the mro and check
        if a valid interface (real or default one) exists.

        """
        test = True
        traceback = {}
        err_path = self.path + '/' + self.name

        if not self.interface and not hasattr(self, 'i_perform'):
            traceback[err_path + '-interface'] = 'Missing interface'
            return False, traceback

        if self.interface:
            i_test, i_traceback = self.interface.check(*args, **kwargs)

            traceback.update(i_traceback)
            test &= i_test

        res = super(InterfaceableTaskMixin, self).check(*args, **kwargs)
        test &= res[0]
        traceback.update(res[1])

        return test, traceback

    def perform(self, *args, **kwargs):
        """Implementation of perform relying on interfaces.

        This method will be considered as the true perform method of the task,
        it will either call the interface perform method or the special
        i_perform method if there is no interface. This is meant to provide
        an easy way to turn a non-interfaced task into an interfaced one :
        - add the mixin as the left most inherited class
        - rename the perform method to i_perform
        - create new interfaces but keep the default 'standard' behaviour.

        NEVER OVERRIDE IT IN SUBCLASSES OTHERWISE YOU WILL BREAK THE
        INTERFACE SYSTEM.

        """
        if self.interface:
            return self.interface.perform(*args, **kwargs)
        else:
            return self.i_perform(*args, **kwargs)

    def answer(self, members, callables):
        """Retrieve informations about a task.

        Reimplemented here to also explore the interface.

        Parameters
        ----------
        members : list(str)
            List of members names whose values should be returned.

        callables : dict(str, callable)
            Dict of name callable to invoke on the task or interface to get
            some infos.

        Returns
        -------
        infos : dict
            Dict holding all the answers for the specified members and
            callables.

        """
        # I assume the interface does not override any task member.
        # For the callables only the not None answer will be updated.
        ancestors = type(self).mro()
        i = ancestors.index(InterfaceableTaskMixin)
        answers = ancestors[i + 1].answer(self, members, callables)

        if self.interface:
            interface_answers = self.interface.answer(members, callables)
            answers.update(interface_answers)
        return answers

    def register_preferences(self):
        """Register the task preferences into the preferences system.

        """
        ancestors = type(self).mro()
        i = ancestors.index(InterfaceableTaskMixin)
        ancestors[i + 1].register_preferences(self)

        if self.interface:
            prefs = self.interface.preferences_from_members()
            self.preferences['interface'] = prefs

    def update_preferences_from_members(self):
        """Update the values stored in the preference system.

        """
        ancestors = type(self).mro()
        i = ancestors.index(InterfaceableTaskMixin)
        ancestors[i + 1].update_preferences_from_members(self)

        if self.interface:
            prefs = self.interface.preferences_from_members()
            self.preferences['interface'] = prefs

    @classmethod
    def build_from_config(cls, config, dependencies):
        """Create a new instance using the provided infos for initialisation.

        Parameters
        ----------
        config : dict(str)
            Dictionary holding the new values to give to the members in string
            format, or dictionnary like for instance with prefs.

        dependencies : dict
            Dictionary holding the necessary classes needed when rebuilding.
            This is assembled by the TaskManager.

        Returns
        -------
        task :
            Newly built task.

        """
        ancestors = cls.mro()
        i = ancestors.index(InterfaceableTaskMixin)
        builder = ancestors[i + 1].build_from_config.__func__
        task = builder(cls, config, dependencies)

        if 'interface' in config:
            inter_class_name = config['interface'].pop('interface_class')
            inter_class = dependencies['interfaces'][inter_class_name]
            task.interface = inter_class.build_from_config(config['interface'],
                                                           dependencies)

        return task

    def _post_setattr_interface(self, old, new):
        """ Observer ensuring the interface always has a valid ref to the task
        and that the interface database entries are added to the task one.

        """
        # XXXX Workaround Atom _DictProxy issue.
        new_entries = dict(self.database_entries)
        if old:
            inter = old
            inter.task = None
            for entry in inter.database_entries:
                new_entries.pop(entry, None)

        if new:
            inter = new
            inter.task = self
            for entry, value in inter.database_entries.iteritems():
                new_entries[entry] = value

        self.database_entries = new_entries


class TaskInterface(HasPrefAtom):
    """Base class to use when writing a task interface.

    The interface should not re-use member names used by the task to avoid
    issue when walking.

    """
    #: Class attribute indicating whether this interface has views or not.
    has_view = False

    #: A reference to which this interface is linked.
    task = Instance(BaseTask)

    #: Name of the class of the interface. Used for persistence purposes.
    interface_class = Unicode().tag(pref=True)

    #: Dict of database entries added by the interface.
    database_entries = Dict()

    def check(self, *args, **kwargs):
        """Check that everything is alright before starting a measurement.

        By default tries to format all members tagged with 'format' and try to
        eval all members tagged with 'eval'. If the tag value is 'Warn', the
        test will considered passed but a traceback entry will be filled.

        """
        res = True
        traceback = {}
        task = self.task
        err_path = task.path + '/' + task.name
        for n, m in tagged_members(self, 'fmt').items():
            try:
                val = task.format_string(getattr(self, n))
                if n in self.database_entries:
                    task.write_in_database(n, val)
            except Exception:
                if m.metadata['fmt'] != 'Warn':
                    res = False
                msg = 'Failed to format %s : %s' % (n, format_exc())
                traceback[err_path + '-' + n] = msg

        for n, m in tagged_members(self, 'feval').items():
            try:
                val = task.format_and_eval_string(getattr(self, n))
                if n in self.database_entries:
                    task.write_in_database(n, val)
            except Exception:
                if m.metadata['feval'] != 'Warn':
                    res = False
                msg = 'Failed to eval %s : %s' % (n, format_exc())
                traceback[err_path + '-' + n] = msg

        return res, traceback

    def perform(self, *args, **kwargs):
        """Method called by the perform method defined on the
        InterfaceableTaskMixin class.

        """
        raise NotImplementedError()

    def answer(self, members, callables):
        """Method used by to retrieve information about a task.

        Parameters
        ----------
        members : list(str)
            List of members names whose values should be returned.

        callables : dict(str, callable)
            Dict of name callable to invoke on the task or interface to get
            some infos.

        Returns
        -------
        infos : dict
            Dict holding all the answers for the specified members and
            callables. Contrary to what happens for task this one will never
            contain None as a value.

        """
        answers = {m: getattr(self, m, None) for m in members}
        answers.update({k: c(self) for k, c in callables.iteritems()})
        for key, val in answers.copy().iteritems():
            if val is None:
                del answers[key]

        return answers

    @classmethod
    def build_from_config(cls, config, dependencies):
        """ Create an interface using the provided dict.

        """
        interface = cls()
        interface.update_members_from_preferences(config)
        return interface

    def _default_interface_class(self):
        """ Default value for the class_name member.

        """
        return type(self).__name__
