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

from atom.api import (Atom, ForwardTyped, Typed, Unicode, Dict, Property,
                      Constant)

from ...utils.traceback import format_exc
from ...utils.atom_util import HasPrefAtom, tagged_members
from .base_tasks import BaseTask
from . import validators


#: Id used to identify dependencies type.
DEP_TYPE = 'ecpy.tasks.interface'


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

    def prepare(self):
        """Prepare both the task and the interface.

        """
        super(InterfaceableMixin, self).prepare()
        if self.interface:
            self.interface.prepare()

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

    def traverse(self, depth=-1):
        """First yield self then interface and finally next values.

        """
        it = super(InterfaceableMixin, self).traverse(depth)
        yield next(it)
        interface = self.interface
        if interface:
            if depth == 0:
                yield interface
            else:
                for i in interface.traverse(depth - 1):
                    yield i

        for c in it:
            yield c

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
        task : BaseTask
            Newly built task.

        """
        new = super(InterfaceableMixin, cls).build_from_config(config,
                                                               dependencies)

        if 'interface' in config:
            iclass = config['interface'].pop('interface_id')
            inter_class = dependencies[DEP_TYPE][iclass]
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

            # Always make the interface the first section.
            if len(self.preferences.sections) > 1:
                ind = self.preferences.sections.index('interface')
                del self.preferences.sections[ind]
                self.preferences.sections.insert(0, 'interface')

    def update_preferences_from_members(self):
        """Update the values stored in the preference system.

        """
        super(InterfaceableTaskMixin, self).update_preferences_from_members()

        if self.interface:
            prefs = self.interface.preferences_from_members()
            self.preferences['interface'] = prefs

            # Always make the interface the first section.
            if len(self.preferences.sections) > 1:
                ind = self.preferences.sections.index('interface')
                del self.preferences.sections[ind]
                self.preferences.sections.insert(0, 'interface')

    def get_error_path(self):
        """Build the path to use when reporting errors during checks.

        """
        return self.path + '/' + self.name

    def _post_setattr_interface(self, old, new):
        """ Observer ensuring the interface always has a valid ref to the task
        and that the interface database entries are added to the task one.

        """
        # HINT Workaround Atom _DictProxy issue.
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
            for entry, value in inter.database_entries.items():
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
        task = self.task
        if task:
            # HINT Workaround Atom _DictProxy issue.
            new_entries = dict(task.database_entries)
            if old:
                inter = old
                inter.parent = None
                for entry in inter.database_entries:
                    new_entries.pop(entry, None)

            if new:
                inter = new
                inter.parent = self
                new_entries.update(inter.database_entries)

            task.database_entries = new_entries


class BaseInterface(HasPrefAtom):
    """Base class to use for interfaces.

    The interface should not re-use member names used by the task to avoid
    issue when walking.

    This class should not be used directly, use one of its subclass.

    """
    #: Identifier for the build dependency collector
    dep_type = Constant(DEP_TYPE).tag(pref=True)

    #: Id of the interface preceded by the ids of all its anchors separated by
    # ':'. Used for persistence purposes.
    interface_id = Unicode().tag(pref=True)

    #: Dict of database entries added by the interface.
    database_entries = Dict()

    def check(self, *args, **kwargs):
        """Check that everything is alright before starting a measurement.

        By default tries to format all members tagged with 'fmt' and try to
        eval all members tagged with 'feval'. If the tag value is 'Warn', the
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
            val = m.metadata['feval']
            if not isinstance(val, validators.Feval):
                res = False
                msg = 'Feval validator is not a subclass validators.Feval'
            else:
                value, f_res, msg = val.check(self, n)
                res &= f_res

            if msg:
                traceback[err_path + '-' + n] = msg
            elif value is not None and n in self.database_entries:
                task.write_in_database(n, value)

        return res, traceback

    def prepare(self):
        """Prepare the interface to be performed.

        This method is called once by the parent task before starting the
        execution.

        """
        pass

    def perform(self, *args, **kwargs):
        """Method called by the parent perform method.

        """
        raise NotImplementedError()

    def traverse(self, depth=-1):
        """Method used by to retrieve information about a task.

        Parameters
        ----------
        depth : int
            How deep should we stop traversing.

        """
        yield self

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
        pack, _ = self.__module__.split('.', 1)
        i_id = pack + '.' + type(self).__name__
        self.interface_id = new.task_id + ':' + i_id if new else i_id


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
        pack, _ = self.__module__.split('.', 1)
        i_id = pack + '.' + type(self).__name__
        if new:
            self.interface_id = self.parent.interface_id + ':' + i_id
        else:
            self.interface_id = i_id
        task_member = self.get_member(str('task'))  # Python 2, Atom 0.x compat
        task_member.reset(self)
