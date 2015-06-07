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

from ast import literal_eval
from traceback import format_exc
from atom.api import Atom, ForwardTyped, Typed, Tuple, Dict, Property

from ..utils.atom_util import HasPrefAtom, tagged_members
from .base_tasks import BaseTask


class InterfaceableMixin(Atom):
    """Base class for mixin used to fabricate interfaceable task or interface.

    This class should not be used directly, use one of its subclass.

    """
    #: A reference to the current interface for the task.
    interface = ForwardTyped(lambda: BaseInterface)

    def check(self, *args, **kwargs):
        """ Check the interface.

        This run the checks of the next parent class in the mro and check
        if a valid interface (real or default one) exists.

        """
        test = True
        traceback = {}
        err_path = self.get_error_path()

        if not self.interface and not hasattr(self, 'i_perform'):
            traceback[err_path + '-interface'] = 'Missing interface'
            return False, traceback

        if self.interface:
            i_test, i_traceback = self.interface.check(*args, **kwargs)

            traceback.update(i_traceback)
            test &= i_test

        res = super(InterfaceableMixin, self).check(*args, **kwargs)
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
        infos : list
            List holding the main object and its interface answers

        """
        # I assume the interface does not override any task member.
        # For the callables only the not None answer will be updated.
        answers = super(InterfaceableMixin, self).answer(members, callables)

        if self.interface:
            interface_answers = self.interface.answer(members, callables)

        return [answers, interface_answers]

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
        new = super(InterfaceableMixin, cls).build_from_config(config,
                                                               dependencies)

        if 'interface' in config:
            iclass = config['interface'].pop('interface_class')
            inter_class = dependencies['interfaces'][literal_eval(iclass)]
            new.interface = inter_class.build_from_config(config['interface'],
                                                          dependencies)

        return new

    def get_error_path(self):
        """Build the path to use when reporting errors during checks.

        """
        raise NotImplementedError()


class InterfaceableTaskMixin(InterfaceableMixin):
    """Mixin class for defining a task using interfaces.

    When defining a new interfaceable task this mixin should always be the
    letf most class when defining the inheritance. This is due to the Python
    Method Resolution Order (mro) and the fact that this mixin must override
    methods defined in tasks.
    ex : MyTaskI(InterfaceableTaskMixin, MyTask):

    """
    def register_preferences(self):
        """Register the task preferences into the preferences system.

        """
        super(InterfaceableTaskMixin, self).register_preferences()

        if self.interface:
            prefs = self.interface.preferences_from_members()
            self.preferences['interface'] = prefs

    def update_preferences_from_members(self):
        """Update the values stored in the preference system.

        """
        super(InterfaceableTaskMixin, self).update_preferences_from_members()

        if self.interface:
            prefs = self.interface.preferences_from_members()
            self.preferences['interface'] = prefs

    def get_error_path(self):
        """Build the path to use when reporting errors during checks.

        """
        return self.path + '/' + self.name

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
            if isinstance(inter, InterfaceableInterfaceMixin):
                inter._post_setattr_interface(None, inter.interface)
            for entry, value in inter.database_entries.iteritems():
                new_entries[entry] = value

        self.database_entries = new_entries


class InterfaceableInterfaceMixin(InterfaceableMixin):
    """Mixin class for defining an interface using interfaces.

    When defining a new interfaceable task this mixin should always be the
    letf most class when defining the inheritance. This is due to the Python
    Method Resolution Order (mro) and the fact that this mixin must override
    methods defined in tasks.
    ex : MyInterface(InterfaceableTaskMixin, Interface):

    """
    def get_error_path(self):
        """Build the path to use when reporting errors during checks.

        """
        try:
            return self.parent.get_error_path() + '/' + type(self).__name__
        except AttributeError:
            return '/'.join((self.task.path, self.task.name,
                             type(self).__name__))

    def preferences_from_members(self):
        """Update the values stored in the preference system.

        """
        prefs = super(InterfaceableInterfaceMixin,
                      self).preferences_from_members()

        if self.interface:
            i_prefs = self.interface.preferences_from_members()
            prefs['interface'] = i_prefs

        return prefs

    def _post_setattr_interface(self, old, new):
        """ Observer ensuring the interface always has a valid ref to the
        parent interface and that the interface database entries are added to
        the task one.

        """
        # XXXX Workaround Atom _DictProxy issue.
        task = self.task
        if task:
            new_entries = dict(task.database_entries)
            if old:
                inter = old
                inter.parent = None
                for entry in inter.database_entries:
                    new_entries.pop(entry, None)

            if new:
                inter = new
                inter.parent = self
                for entry, value in inter.database_entries.iteritems():
                    new_entries[entry] = value

            task.database_entries = new_entries


class BaseInterface(HasPrefAtom):
    """Base class to use for interfaces.

    The interface should not re-use member names used by the task to avoid
    issue when walking.

    This class should not be used directly, use one of its subclass.

    """
    #: Class attribute indicating whether this interface has views or not.
    has_view = False

    #: Name of the class of the interface and anchor (ie task or interface with
    #: this interface is used with). Used for persistence purposes.
    interface_class = Tuple().tag(pref=True)

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
        """Method called by the parent perform method.

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

        return answers

    @classmethod
    def build_from_config(cls, config, dependencies):
        """ Create an interface using the provided dict.

        """
        interface = cls()
        interface.update_members_from_preferences(config)
        return interface


class TaskInterface(BaseInterface):
    """Base class to use when writing a task interface.

    The interface should not re-use member names used by the task to avoid
    issue when walking.

    """
    #: A reference to the task to which this interface is linked.
    task = Typed(BaseTask)

    def _post_setattr_task(self, old, new):
        """Update the interface anchor when the task is set.

        """
        self.interface_class = ((type(self).__name__, [new.task_class]) if new
                                else ())


class IInterface(BaseInterface):
    """Base class to use when writing an interface interface.

    The interface should not re-use member names used by the task or parent
    interfaces to avoid issue when walking.

    """
    #: A reference to the parent interface to which this interface is linked.
    parent = Typed(BaseInterface)

    #: Direct access to the task, which acts as a root parent.
    task = Property(cached=True)

    @task.getter
    def _get_task(self):
        return self.parent.task

    def _post_setattr_parent(self, old, new):
        """Reset the task property and update the interface anchor.

        """
        if new:
            self.interface_class = (type(self).__name__,
                                    self.parent.interface_class[1] +
                                    [self.parent.interface_class[0]])
        else:
            self.interface_anchor = ()
        task_member = self.get_member(str('task'))  # Python 2, Atom 0.x compat
        task_member.reset(self)
