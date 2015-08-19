# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Definition of the base tasks.

The base tasks define how task interact between them and with the database, how
ressources can be shared and how preferences are handled.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import os
import logging
import threading
from atom.api import (Atom, Int, Bool, Value, Unicode, List,
                      ForwardTyped, Typed, Callable, Dict, Signal,
                      Tuple, Coerced, Constant, set_default)
from configobj import Section, ConfigObj
from inspect import cleandoc
from textwrap import fill
from copy import deepcopy
from traceback import format_exc
from future.utils import istext
from future.builtins import str as text
from multiprocessing.synchronize import Event
from datetime import date
from collections import Iterable

from ..utils.atom_util import (tagged_members, update_members_from_preferences)
from ..utils.container_change import ContainerChange
from .tools.database import TaskDatabase
from .tools.decorators import (make_parallel, make_wait, make_stoppable,
                               smooth_crash)
from .tools.string_evaluation import safe_eval
from .tools.shared_resources import (SharedCounter, ThreadPoolResource,
                                     InstrsResource, FilesResource)


#: Prefix for placeholders in string formatting and evaluation.
PREFIX = '_a'


#: Id used to identify dependencies type.
DEP_TYPE = 'ecpy.task'


class BaseTask(Atom):
    """Base  class defining common members of all Tasks.

    This class basically defines the minimal skeleton of a Task in term of
    members and methods.

    """
    #: Identifier for the build dependency collector
    dep_type = Constant(DEP_TYPE).tag(pref=True)

    #: Name of the class, used for persistence.
    task_class = Unicode().tag(pref=True)

    #: Name of the task this should be unique in hierarchy.
    name = Unicode().tag(pref=True)

    #: Depth of the task in the hierarchy. this should not be manipulated
    #: directly by user code.
    depth = Int()

    #: Reference to the Section in which the task stores its preferences.
    preferences = Typed(Section)

    #: Reference to the database used by the task to exchange information.
    database = Typed(TaskDatabase)

    #: Entries the task declares in the database and the associated default
    #: values. This should be copied and re-assign when modified not modfied
    #: in place.
    database_entries = Dict(Unicode(), Value())

    #: Path of the task in the hierarchy. This refers to the parent task and
    #: is used when writing in the database.
    path = Unicode()

    #: Reference to the root task in the hierarchy.
    root = ForwardTyped(lambda: RootTask)

    #: Refrence to the parent task.
    parent = ForwardTyped(lambda: BaseTask)

    #: Unbound method called when the task is asked to do its job. This is
    #: basically the perform method but wrapped with useful stuff such as
    #: interruption check or parallel, wait features.
    perform_ = Callable()

    #: Flag indicating if this task can be stopped.
    stoppable = Bool(True).tag(pref=True)

    #: Dictionary indicating whether the task is executed in parallel
    #: ('activated' key) and which is pool it belongs to ('pool' key).
    parallel = Dict(Unicode()).tag(pref=True)

    #: Dictionary indicating whether the task should wait on any pool before
    #: performing its job. Three valid keys can be used :
    #: - 'activated' : a bool indicating whether or not to wait.
    #: - 'wait' : the list should then specify which pool should be waited.
    #: - 'no_wait' : the list should specify which pool not to wait on.
    wait = Dict(Unicode()).tag(pref=True)

    #: List of access exception in the database. This should not be manipulated
    #: by user code.
    access_exs = Dict().tag(pref=True)

    def perform(self):
        """ Main method of the task called when the measurement is performed.

        """
        raise NotImplementedError(
            fill(cleandoc('''This method should be implemented by subclasses of
            BaseTask. This method is called when the program requires the task
            to perform its job.''')))

    def check(self, *args, **kwargs):
        """Check that everything is alright before starting a measurement.

        By default tries to format all members tagged with 'fmt' and try to
        eval all members tagged with 'feval'. If the tag value is 'Warn', the
        will considered passed but a traceback entry will be filled.
        The perform_ member is also computed at this time.

        """
        res = True
        traceback = {}
        err_path = self.path + '/' + self.name
        for n, m in tagged_members(self, 'fmt').items():
            try:
                val = self.format_string(getattr(self, n))
                if n in self.database_entries:
                    self.write_in_database(n, val)
            except Exception:
                if m.metadata['fmt'] != 'Warn':
                    res = False
                msg = 'Failed to format %s : %s' % (n, format_exc())
                traceback[err_path + '-' + n] = msg

        for n, m in tagged_members(self, 'feval').items():
            try:
                val = self.format_and_eval_string(getattr(self, n))
                if n in self.database_entries:
                    self.write_in_database(n, val)
            except Exception:
                if m.metadata['feval'] != 'Warn':
                    res = False
                msg = 'Failed to eval %s : %s' % (n, format_exc())
                traceback[err_path + '-' + n] = msg

        self._build_perform_()
        return res, traceback

    def register_preferences(self):
        """Create the task entries in the preferences object.

        """
        raise NotImplementedError()

    def update_preferences_from_members(self):
        """Update the entries in the preference object.

        """
        raise NotImplementedError()

    @classmethod
    def build_from_config(cls, config, dependencies):
        """Create a new instance using the provided infos for initialisation.

        Parameters
        ----------
        config : dict(str)
            Dictionary holding the new values to give to the members in string
            format, or dictionnary like for instance with prefs.

        dependencies : dict
            Dictionary holding the necessary classes needed when rebuilding..

        """
        raise NotImplementedError()

    def traverse(self, depth=-1):
        """Yield a task and all of its components.

        The base implementation simply yields the task itself.

        Parameters
        ----------
        depth : int
            How deep should we explore the tree of tasks. When this number
            reaches zero deeper children should not be explored but simply
            yielded.

        """
        yield self

    def register_in_database(self):
        """ Register the task entries into the database.

        """
        if self.database_entries:
            for entry in self.database_entries:
                # Perform a deepcopy of the entry value as I don't want to
                # alter that default value when dealing with the database later
                # on (apply for list and dict).
                value = deepcopy(self.database_entries[entry])
                self.write_in_database(entry, value)

            for access_ex, level in self.access_exs.items():
                self._add_access_exception(access_ex, level)

    def unregister_from_database(self):
        """ Remove the task entries from the database.

        """
        if self.database_entries:
            for entry in self.database_entries:
                self.database.delete_value(self.path, self._task_entry(entry))

            for access_ex, level in self.access_exs.items():
                self._remove_access_exception(access_ex, level)

    def add_access_exception(self, entry, level):
        """Add an access exception for an entry.

        Parameters
        ----------
        entry : unicode
            Name of the task database entry for which to add an exception.

        level : int
            Number of hierarchical levels to go up when adding the exception.

        """
        self._add_access_exception(entry, level)
        access_exs = self.access_exs.copy()
        access_exs[entry] = level
        self.access_exs = access_exs

    def modify_access_exception(self, entry, new):
        """Modify the level of an existing access exception.

        Parameters
        ----------
        entry : unicode
            Name of the task database entry for which to modify an exception.

        new : int
            New level for the access exception.

        """
        access_exs = self.access_exs.copy()
        old = access_exs[entry]
        access_exs[entry] = new
        full_name = self._task_entry(entry)

        parent = self
        while old:
            parent = parent.parent
            old -= 1
        self.database.remove_access_exception(parent.path,
                                              full_name)

        parent = self
        while new:
            parent = parent.parent
            new -= 1
        self.database.add_access_exception(parent.path, self.path, full_name)

        self.access_exs = access_exs

    def remove_access_exception(self, entry):
        """Remove an access exception .

        Parameters
        ----------
        entry : unicode
            Name of the task database entry for which to remove an exception.

        """
        access_exs = self.access_exs.copy()
        level = access_exs.pop(entry)
        self.access_exs = access_exs
        self._remove_access_exception(entry, level)

    def write_in_database(self, name, value):
        """Write a value to the right database entry.

        This method build a task specific database entry from the name
        and the name argument and set the database entry to the specified
        value.

        Parameters
        ----------
        name : str
            Simple name of the entry whose value should be set, ie no task name
            required.

        value:
            Value to give to the entry.

        """
        value_name = self._task_entry(name)
        return self.database.set_value(self.path, value_name, value)

    def get_from_database(self, full_name):
        """Access to a database value using full name.

        Parameters
        ----------
        full_name : str
            Full name of the database entry, ie name + '_' + entry,
            where name is the name of the task that wrote the value in
            the database.

        """
        return self.database.get_value(self.path, full_name)

    def remove_from_database(self, full_name):
        """Delete a database entry using its full name.

        Parameters
        ----------
        full_name : str
            Full name of the database entry, ie name + '_' + entry,
            where name is the name of the task that wrote the value in
            the database.

        """
        return self.database.delete_value(self.path, full_name)

    def list_accessible_database_entries(self):
        """List the database entries accessible from this task.

        """
        return self.database.list_accessible_entries(self.path)

    def format_string(self, string):
        """Replace values between {} by their corresponding database value.

        Parameters
        ----------
        string : str
            The string to format using the current values of the database.

        Returns
        -------
        formatted : str
            Formatted version of the input.

        """
        # If a cache evaluation of the string already exists use it.
        if string in self._format_cache:
            preformatted, ids = self._format_cache[string]
            vals = self.database.get_values_by_index(ids, PREFIX)
            return preformatted.format(**vals)

        # Otherwise if we are in running mode build a cache formatting.
        elif self.database.running:
            database = self.database
            aux_strings = string.split('{')
            if len(aux_strings) > 1:
                elements = [el
                            for aux in aux_strings
                            for el in aux.split('}')]
                database_indexes = database.get_entries_indexes(self.path,
                                                                elements[1::2])
                str_to_format = ''
                length = len(elements)
                for i in range(0, length, 2):
                    if i + 1 < length:
                        repl = PREFIX + str(database_indexes[elements[i + 1]])
                        str_to_format += elements[i] + '{' + repl + '}'
                    else:
                        str_to_format += elements[i]

                indexes = database_indexes.values()
                self._format_cache[string] = (str_to_format, indexes)
                vals = self.database.get_values_by_index(indexes, PREFIX)
                return str_to_format.format(**vals)
            else:
                self._format_cache[string] = (string, [])
                return string

        # In edition mode simply perfom the formatting as execution time is not
        # critical.
        else:
            database = self.database
            aux_strings = string.split('{')
            if len(aux_strings) > 1:
                elements = [el
                            for aux in aux_strings
                            for el in aux.split('}')]
                replacement_values = [database.get_value(self.path, key)
                                      for key in elements[1::2]]
                str_to_format = ''
                for key in elements[::2]:
                    str_to_format += key + '{}'

                str_to_format = str_to_format[:-2]

                return str_to_format.format(*replacement_values)
            else:
                return string

    def format_and_eval_string(self, string):
        """ Replace values in {} by their corresponding database value and eval

        Parameters
        ----------
        string : str
            The string to eval using the current values of the database.

        Returns
        -------
        formatted : str
            Formatted version of the input.

        """
        # If a cache evaluation of the string already exists use it.
        if string in self._eval_cache:
            preformatted, ids = self._eval_cache[string]
            vals = self.database.get_values_by_index(ids, PREFIX)
            return safe_eval(preformatted, vals)

        # Otherwise if we are in running mode build a cache evaluation.
        elif self.database.running:
            database = self.database
            aux_strings = string.split('{')
            if len(aux_strings) > 1:
                elements = [el
                            for aux in aux_strings
                            for el in aux.split('}')]
                database_indexes = database.get_entries_indexes(self.path,
                                                                elements[1::2])
                str_to_eval = ''
                length = len(elements)
                for i in range(0, length, 2):
                    if i + 1 < length:
                        repl = PREFIX + str(database_indexes[elements[i + 1]])
                        str_to_eval += elements[i] + repl
                    else:
                        str_to_eval += elements[i]

                indexes = database_indexes.values()
                self._eval_cache[string] = (str_to_eval, indexes)
                vals = self.database.get_values_by_index(indexes, PREFIX)
                return safe_eval(str_to_eval, vals)
            else:
                self._eval_cache[string] = (string, [])
                return safe_eval(string, {})

        # In edition mode simply perfom the evaluation as execution time is not
        # critical and as the database has not been collapsed to an indexed
        # representation.
        else:
            database = self.database
            aux_strings = string.split('{')
            if len(aux_strings) > 1:
                elements = [el
                            for aux in aux_strings
                            for el in aux.split('}')]
                replacement_token = [PREFIX + str(i)
                                     for i in xrange(len(elements[1::2]))]
                repl = {PREFIX + str(i): database.get_value(self.path,
                                                            key)
                        for i, key in enumerate(elements[1::2])}
                str_to_format = ''
                for key in elements[::2]:
                    str_to_format += key + '{}'

                str_to_format = str_to_format[:-2]

                expr = str_to_format.format(*replacement_token)
                return safe_eval(expr, repl)
            else:
                return safe_eval(string, {})

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Dictionary storing infos necessary to perform fast formatting.
    #: Only used in running mode.
    _format_cache = Dict()

    #: Dictionary storing infos necessary to perform fast evaluation.
    #: Only used in running mode.
    _eval_cache = Dict()

    def _build_perform_(self):
        """Make perform_ refects the parallel/wait settings.

        """
        perform_func = self.perform.__func__
        parallel = self.parallel
        if parallel.get('activated') and parallel.get('pool'):
            perform_func = make_parallel(perform_func, parallel['pool'])

        wait = self.wait
        if wait.get('activated'):
            perform_func = make_wait(perform_func,
                                     wait.get('wait'),
                                     wait.get('no_wait'))

        if self.stoppable:
            self.perform_ = make_stoppable(perform_func)
        else:
            self.perform_ = perform_func

    def _default_task_class(self):
        """Default value for the task_class member.

        """
        return self.__class__.__name__

    def _post_setattr_database_entries(self, old, new):
        """Update the database content each time the database entries change.

        """
        if old and self.database:
            added = set(new) - set(old)
            removed = set(old) - set(new)
            for entry in removed:
                full_name = self._task_entry(entry)
                self.remove_from_database(full_name)
            for entry in added:
                new_value = deepcopy(self.database_entries[entry])
                self.write_in_database(entry, new_value)

            for r in [r for r in removed if r in self.access_exs]:
                self.remove_access_exception(r)

    def _post_setattr_name(self, old, new):
        """Update the database entries as they use the task name.

        """
        if not old or not self.database:
            return

        olds = [old + '_' + e for e in self.database_entries]
        news = [new + '_' + e for e in self.database_entries]
        old_access = {old + '_' + k: v for k, v in self.access_exs.items()
                      if old + '_' + k in olds}
        self.database.rename_values(self.path, olds, news,
                                    old_access)

    def _add_access_exception(self, entry, level):
        """Add an access exception without modifying the access_exs member.

        """
        parent = self
        while level:
            parent = parent.parent
            level -= 1
        self.database.add_access_exception(parent.path, self.path,
                                           self._task_entry(entry))

    def _remove_access_exception(self, entry, level):
        """Remove the access without modifying the access_exs member.

        """
        parent = self
        while level:
            parent = parent.parent
            level -= 1
        full_name = self._task_entry(entry)
        self.database.remove_access_exception(parent.path, full_name)

    def _task_entry(self, entry):
        """Build the full name of an entry for a task.

        """
        return self.name + '_' + entry


class SimpleTask(BaseTask):
    """ Task with no child task, written in pure Python.

    This class is mainly used to avoid having a linear ancestry relationship
    between SimpleTask and ComplexTask.

    """
    #: Class attribute specifying if that task can be used in a loop
    loopable = False

    def register_preferences(self):
        """Register the task preferences into the preferences system.

        """
        self.preferences.clear()
        for name in tagged_members(self, 'pref'):
            val = getattr(self, name)
            if istext(val):
                self.preferences[name] = val
            else:
                self.preferences[name] = repr(val)

    update_preferences_from_members = register_preferences

    @classmethod
    def build_from_config(cls, config, dependencies):
        """ Create a new instance using the provided infos for initialisation.

        Parameters
        ----------
        config : dict(str)
            Dictionary holding the new values to give to the members in string
            format, or dictionnary like for instance with prefs.

        dependencies : dict
            Dictionary holding the necessary classes needed when rebuilding.

        """
        task = cls()
        update_members_from_preferences(task, config)

        return task


class ComplexTask(BaseTask):
    """Task composed of several subtasks.

    """
    #: List of all the children of the task. The list should not be manipulated
    #: directly by user code.
    #: The tag 'child' is used to mark that a member can contain child tasks
    #: and is used gather children for operation which must occur on all of
    #: them.
    children = List().tag(child=100)

    #: Signal emitted when the list of children change, the payload will be a
    # ContainerChange instance.
    children_changed = Signal()

    #: Flag indicating whether or not the task has a root task.
    has_root = Bool(False)

    def perform(self):
        """Run sequentially all child tasks.

        """
        for child in self.children:
            child.perform_(child)

    def check(self, *args, **kwargs):
        """Run test of all child tasks.

        """
        test, traceback = super(ComplexTask, self).check(*args, **kwargs)
        for child in self.gather_children():
            check = child.check(*args, **kwargs)
            test = test and check[0]
            traceback.update(check[1])

        return test, traceback

    def add_child_task(self, index, child):
        """Add a child task at the given index.

        Parameters
        ----------
        index : int
            Index at which to insert the new child task.

        task : BaseTask
            Task to insert in the list of children task.

        """
        self.children.insert(index, child)

        # In the absence of a root task do nothing else than inserting the
        # child.
        if self.has_root:
            child.depth = self.depth + 1
            child.database = self.database
            child.path = self._child_path()

            # Give him its root so that it can proceed to any child
            # registration it needs to.
            child.parent = self
            child.root = self.root

            # Ask the child to register in database
            child.register_in_database()

            # Register anew preferences to keep the right ordering for the
            # children
            self.register_preferences()

            change = ContainerChange(obj=self, name='children',
                                     added=[(index, child)])
            self.children_changed(change)

    def move_child_task(self, old, new):
        """Move a child task.

        Parameters
        ----------
        old : int
            Index at which the child to move is currently located.

        new : BaseTask
            Index at which to insert the child task.

        """
        child = self.children.pop(old)
        self.children.insert(new, child)

        # In the absence of a root task do nothing else than moving the
        # child.
        if self.has_root:
            # Register anew preferences to keep the right ordering for the
            # children
            self.register_preferences()

            change = ContainerChange(obj=self, name='children',
                                     moved=[(old, new, child)])
            self.children_changed(change)

    def remove_child_task(self, index):
        """Remove a child task from the children list.

        Parameters
        ----------
        index : int
            Index at which the child to remove is located.

        """
        child = self.children.pop(index)

        # Cleanup database, update preferences
        child.unregister_from_database()
        child.root = None
        child.parent = None
        self.register_preferences()

        change = ContainerChange(obj=self, name='children',
                                 removed=[(index, child)])
        self.children_changed(change)

    def gather_children(self):
        """Build a flat list of all children task.

        Children tasks are ordered according to their 'child' tag value.

        """
        children = []
        tagged = tagged_members(self, 'child')
        for name in sorted(tagged, key=lambda m: tagged[m].metadata['child']):

            child = getattr(self, name)
            if child:
                if isinstance(child, Iterable):
                    children.extend(child)
                else:
                    children.append(child)

        return children

    def traverse(self, depth=-1):
        """Reimplemented to yield all child task.

        """
        yield self

        if depth == 0:
            for c in self.gather_children():
                if c:
                    yield c

        else:
            for c in self.gather_children():
                if c:
                    for subc in c.traverse(depth - 1):
                        yield subc

    def register_in_database(self):
        """Create a node in the database and register all entries.

        This method registers both the task entries and all the tasks tagged
        as child.

        """
        super(ComplexTask, self).register_in_database()
        self.database.create_node(self.path, self.name)

        # ComplexTask defines children so we always get something
        for child in self.gather_children():
            child.register_in_database()

    def unregister_from_database(self):
        """Unregister all entries and delete associated database node.

        This method unregisters both the task entries and all the tasks tagged
        as child.

        """
        super(ComplexTask, self).unregister_from_database()

        for child in self.gather_children():
            child.unregister_from_database()

        self.database.delete_node(self.path, self.name)

    def register_preferences(self):
        """Register the task preferences into the preferences system.

        This method registers both the task preferences and all the
        preferences of the tasks tagged as child.

        """
        self.preferences.clear()
        members = self.members()
        for name in members:
            # Register preferences.
            meta = members[name].metadata
            if meta and 'pref' in meta:
                val = getattr(self, name)
                if isinstance(val, basestring):
                    self.preferences[name] = val
                else:
                    self.preferences[name] = repr(val)

            # Find all tagged children.
            elif meta and 'child' in meta:
                child = getattr(self, name)
                if child:
                    if isinstance(child, list):
                        for i, aux in enumerate(child):
                            child_id = name + '_{}'.format(i)
                            self.preferences[child_id] = {}
                            aux.preferences = \
                                self.preferences[child_id]
                            aux.register_preferences()
                    else:
                        self.preferences[name] = {}
                        child.preferences = self.preferences[name]
                        child.register_preferences()

    def update_preferences_from_members(self):
        """Update the values stored in the preference system.

        This method updates both the task preferences and all the
        preferences of the tasks tagged as child.

        """
        for name in tagged_members(self, 'pref'):
            val = getattr(self, name)
            if isinstance(val, basestring):
                self.preferences[name] = val
            else:
                self.preferences[name] = repr(val)

        for child in self.gather_children():
            child.update_preferences_from_members()

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
            Newly created and initiliazed task.

        Notes
        -----
        This method is fairly powerful and can handle a lot of cases so
        don't override it without checking that it works.

        """
        task = cls()
        update_members_from_preferences(task, config)
        for name, member in tagged_members(task, 'child').items():

            if isinstance(member, List):
                i = 0
                pref = name + '_{}'
                validated = []
                while True:
                    child_name = pref.format(i)
                    if child_name not in config:
                        break
                    child_config = config[child_name]
                    child_class_name = child_config.pop('task_class')
                    child_cls = dependencies[DEP_TYPE][child_class_name]
                    child = child_cls.build_from_config(child_config,
                                                        dependencies)
                    validated.append(child)
                    i += 1

            else:
                if name not in config:
                    continue
                child_config = config[name]
                child_class_name = child_config.pop('task_class')
                child_class = dependencies[DEP_TYPE][child_class_name]
                validated = child_class.build_from_config(child_config,
                                                          dependencies)

            setattr(task, name, validated)

        return task

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Last removed child and list of database access exceptions attached to
    #: it and necessity to observe its _access_exs.
    _last_removed = Tuple(default=(None, None, False))

    #: Last access exceptions desactivated from a child.
    _last_exs = Coerced(set)

    #: List of access_exs, linked to access exs in child, disabled because
    #: child disabled some access_exs.
    _disabled_exs = List()

    def _child_path(self):
        """Convenience function returning the path to set for child task.

        """
        return self.path + '/' + self.name

    def _update_children_path(self):
        """Update the path of all children.

        """
        for child in self.gather_children():
            child.path = self._child_path()
            if isinstance(child, ComplexTask):
                child._update_children_path()

    def _post_setattr_name(self, old, new):
        """Handle the task being renamed at runtime.

        If the task is renamed at runtime, it means that the path of all the
        children task is now obselete and that the database node
        of this task must be renamed (database handles the exception.

        """
        if old and self.database:
            super(ComplexTask, self)._post_setattr_name(old, new)
            self.database.rename_node(self.path, old, new)

            # Update the path of all children.
            self._update_children_path()

    def _post_setattr_root(self, old, new):
        """Make sure that all children get all the info they need to behave
        correctly when the task get its root parent (ie the task is now
        in a 'correct' environnement).

        """
        if new is None:
            return

        self.has_root = True
        for child in self.gather_children():
            child.depth = self.depth + 1
            child.database = self.database
            child.path = self.path + '/' + self.name

            # Give him its root so that it can proceed to any child
            # registration it needs to.
            child.parent = self
            child.root = self.root


class RootTask(ComplexTask):
    """Special task which is always the root of a measurement.

    On this class and this class only perform can and should be called
    directly.

    """
    #: Path to which log infos, preferences, etc should be written by default.
    default_path = Unicode('').tag(pref=True)

    #: Dict storing data needed at execution time (ex: drivers classes)
    run_time = Dict()

    #: Inter-process event signaling the task it should stop execution.
    should_stop = Typed(Event)

    #: Inter-process event signaling the task it should pause execution.
    should_pause = Typed(Event)

    #: Inter-process event signaling the task is paused.
    paused = Typed(Event)

    #: Inter-Thread event signaling the main thread is done, handling the
    #: measure resuming.
    resume = Value()

    #: Dictionary used to store references to resources that may need to be
    #: shared between task and which must be released when all tasks have been
    #: performed.
    #: Each key is associated to a different kind of resource. Resources must
    #: be stored in SharedDict subclass.
    #: By default three kind of resources exists:
    #: - threads : currently running threads grouped by pool.
    #:   ({pool: [threads, releaser]})
    #: - instrs : used instruments referenced by profiles.
    #: - files : currently opened files by path.
    resources = Dict()

    #: Counter keeping track of the active threads.
    active_threads_counter = Typed(SharedCounter, kwargs={'count': 1})

    #: Counter keeping track of the paused threads.
    paused_threads_counter = Typed(SharedCounter, ())

    #: Thread from which the perform method has been called.
    thread_id = Int()

    # Setting default values for the root task.
    has_root = set_default(True)

    # Those must not be modified so freeze them
    name = Constant('Root')
    depth = Constant(0)
    path = Constant('root')
    database_entries = set_default({'default_path': ''})

    def __init__(self, *args, **kwargs):
        self.preferences = ConfigObj(indent_type='    ')
        self.database = TaskDatabase()
        super(RootTask, self).__init__(*args, **kwargs)
        self.register_in_database()
        self.root = self
        self.parent = self
        self.active_threads_counter.observe('count', self._state)
        self.paused_threads_counter.observe('count', self._state)

    def check(self, *args, **kwargs):
        """Check that the default path is a valid directory.

        """
        traceback = {}
        test = True
        if not os.path.isdir(self.default_path):
            test = False
            traceback[self.path + '/' + self.name] =\
                'The provided default path is not a valid directory'
        self.write_in_database('default_path', self.default_path)
        check = super(RootTask, self).check(*args, **kwargs)
        test = test and check[0]
        traceback.update(check[1])
        return test, traceback

    @smooth_crash
    def perform(self):
        """ Run sequentially all child tasks, and close ressources.

        """
        self.thread_id = threading.current_thread().ident
        try:
            for child in self.children:
                child.perform_(child)
        except Exception:
            log = logging.getLogger(__name__)
            mes = 'The following unhandled exception occured:'
            log.exception(mes)
            self.should_stop.set()
        finally:
            self.release_resources()

    def release_resources(self):
        """Release all the resources used by tasks.

        """
        for _, resource in self.resources.items():
            resource.release()

    def register_in_database(self):
        """Don't create a node for the root task.

        """
        BaseTask.register_in_database(self)

        # ComplexTask defines children so we always get something
        for child in self.gather_children():
            child.register_in_database()

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    def _default_task_class(self):
        return ComplexTask.__name__

    def _default_resume(self):
        return threading.Event()

    def _child_path(self):
        """Overriden here to not add the task name.

        """
        return self.path

    def _task_entry(self, entry):
        """Do not prepend the name of the root task.

        """
        return entry

    def _state(self, change):
        """Determine whether the task is paused or not.

        This is done by checking the number of active and paused thread and
        setting accordingly the paused event.

        """
        p_count = self.paused_threads_counter.count
        a_count = self.active_threads_counter.count
        if a_count == p_count:
            self.paused.set()

        if p_count == 0:
            self.paused.clear()

    def _default_resources(self):
        """Default resources.

        """
        return {'threads': ThreadPoolResource(),
                'instrs': InstrsResource(),
                'files': FilesResource()}
