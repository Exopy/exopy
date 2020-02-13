# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Definition of the base tasks.

The base tasks define how task interact between them and with the database, how
ressources can be shared and how preferences are handled.

"""
import os
import logging
import threading
from multiprocessing.synchronize import Event
from collections import Iterable
from inspect import cleandoc
from textwrap import fill
from copy import deepcopy
from types import MethodType
from cProfile import Profile
from operator import attrgetter

from atom.api import (Atom, Int, Bool, Value, Str, List,
                      ForwardTyped, Typed, Callable, Dict, Signal,
                      Tuple, Coerced, Constant, set_default)
from configobj import Section, ConfigObj

from ...utils.traceback import format_exc
from ...utils.atom_util import (tagged_members, member_to_pref,
                                update_members_from_preferences)
from ...utils.container_change import ContainerChange
from .database import TaskDatabase
from .decorators import (make_parallel, make_wait, make_stoppable,
                         smooth_crash)
from .string_evaluation import safe_eval
from .shared_resources import (SharedCounter, ThreadPoolResource,
                               InstrsResource, FilesResource)
from . import validators

#: Prefix for placeholders in string formatting and evaluation.
PREFIX = '_a'


#: Id used to identify dependencies type.
DEP_TYPE = 'exopy.task'


class BaseTask(Atom):
    """Base  class defining common members of all Tasks.

    This class basically defines the minimal skeleton of a Task in term of
    members and methods.

    Notes
    -----
    A number of the member used by the task have a definite meaning only when
    a root is present. They are listed below:

    - depth
    - path
    - database
    - parent

    """
    #: Identifier for the build dependency collector
    dep_type = Constant(DEP_TYPE).tag(pref=True)

    #: Name of the class, used for persistence.
    task_id = Str().tag(pref=True)

    #: Name of the task this should be unique in hierarchy.
    name = Str().tag(pref=True)

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
    database_entries = Dict(Str(), Value())

    #: Path of the task in the hierarchy. This refers to the parent task and
    #: is used when writing in the database.
    path = Str()

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
    parallel = Dict(Str()).tag(pref=True)

    #: Dictionary indicating whether the task should wait on any pool before
    #: performing its job. Three valid keys can be used :
    #: - 'activated' : a bool indicating whether or not to wait.
    #: - 'wait' : the list should then specify which pool should be waited.
    #: - 'no_wait' : the list should specify which pool not to wait on.
    wait = Dict(Str()).tag(pref=True)

    #: Dict of access exception in the database. This should not be manipulated
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
        eval all members tagged with 'feval'.

        """
        res = True
        traceback = {}
        err_path = self.get_error_path()
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
                self.write_in_database(n, value)

        return res, traceback

    def prepare(self):
        """Prepare the task to be performed.

        This method is called once by the root task before starting the
        execution of its children tasks. By default it simply build the
        perform\_ method by wrapping perform with the appropriate decorators.
        This method can be overridden to execute other actions, however keep in
        my mind that those actions must not depende on the state of the system
        (no link to database).

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
            perform_func = make_stoppable(perform_func)

        self.perform_ = MethodType(perform_func, self)

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
            New level for the access exception. If this is not strictly
            positive the access exception is simply removed.

        """
        access_exs = self.access_exs.copy()
        old = access_exs[entry]
        if new > 0:
            access_exs[entry] = new
        else:
            del access_exs[entry]
        full_name = self._task_entry(entry)

        parent = self
        while old:
            parent = parent.parent
            old -= 1
        self.database.remove_access_exception(parent.path,
                                              full_name)

        if new > 0:
            parent = self
            while new:
                parent = parent.parent
                new -= 1
            self.database.add_access_exception(parent.path, self.path,
                                               full_name)

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
        value : object
            Evaluated version of the input.

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
                                     for i in range(len(elements[1::2]))]
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

    def get_error_path(self):
        """Build the path to use when reporting errors during checks.

        """
        return self.path + '/' + self.name

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Dictionary storing infos necessary to perform fast formatting.
    #: Only used in running mode.
    _format_cache = Dict()

    #: Dictionary storing infos necessary to perform fast evaluation.
    #: Only used in running mode.
    _eval_cache = Dict()

    def _default_task_id(self):
        """Default value for the task_id member.

        """
        pack, _ = self.__module__.split('.', 1)
        return pack + '.' + type(self).__name__

    def _post_setattr_database_entries(self, old, new):
        """Update the database content each time the database entries change.

        """
        if self.database:
            new = set(new)
            old = set(old) if old else set()
            added = new - old
            removed = old - new
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
        for name, member in tagged_members(self, 'pref').items():
            val = getattr(self, name)
            self.preferences[name] = member_to_pref(self, member, val)

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
    #: and is used to gather children for operation which must occur on all of
    #: them.
    children = List().tag(child=100)

    #: Signal emitted when the list of children change, the payload will be a
    #: ContainerChange instance.
    #: The tag 'child_notifier' is used to mark that a member emmit
    #: notifications about modification of another 'child' member. This allow
    #: editors to correctly track all of those.
    children_changed = Signal().tag(child_notifier='children')

    def perform(self):
        """Run sequentially all child tasks.

        """
        for child in self.children:
            child.perform_()

    def check(self, *args, **kwargs):
        """Run test of all child tasks.

        """
        test, traceback = super(ComplexTask, self).check(*args, **kwargs)
        for child in self.gather_children():
            try:
                check = child.check(*args, **kwargs)
                test = test and check[0]
                traceback.update(check[1])
            except Exception:
                test = False
                msg = 'An exception occured while running check :\n%s'
                traceback[child.path + '/' + child.name] = msg % format_exc()

        return test, traceback

    def prepare(self):
        """Overridden to prepare also children tasks.

        """
        super(ComplexTask, self).prepare()
        for child in self.gather_children():
            child.prepare()

    def add_child_task(self, index, child):
        """Add a child task at the given index.

        Parameters
        ----------
        index : int
            Index at which to insert the new child task.

        child : BaseTask
            Task to insert in the list of children task.

        """
        self.children.insert(index, child)

        # In the absence of a root task do nothing else than inserting the
        # child.
        if self.root is not None:
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
        if self.root is not None:
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
        child.database = None
        self.register_preferences()

        change = ContainerChange(obj=self, name='children',
                                 removed=[(index, child)])
        self.children_changed(change)

    def gather_children(self):
        """Build a flat list of all children task.

        Children tasks are ordered according to their 'child' tag value.

        Returns
        -------
        children : list
            List of all the task children.

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
        for name, member in tagged_members(self, 'pref').items():
            # Register preferences.
            val = getattr(self, name)
            self.preferences[name] = member_to_pref(self, member, val)

        # Find all tagged children.
        for name in tagged_members(self, 'child'):
            child = getattr(self, name)
            if child:
                if isinstance(child, Iterable):
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
        for name, member in tagged_members(self, 'pref').items():
            val = getattr(self, name)
            self.preferences[name] = member_to_pref(self, member, val)

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
        task : BaseTask
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
                    child_class_name = child_config.pop('task_id')
                    child_cls = dependencies[DEP_TYPE][child_class_name]
                    child = child_cls.build_from_config(child_config,
                                                        dependencies)
                    validated.append(child)
                    i += 1

            else:
                if name not in config:
                    continue
                child_config = config[name]
                child_class_name = child_config.pop('task_id')
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
        children task is now obsolete and that the database node
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
            self.database = None
            for child in self.gather_children():
                child.root = None
                child.database = None
            return

        for child in self.gather_children():
            child.depth = self.depth + 1
            child.database = self.database
            child.path = self._child_path()

            # Give him its root so that it can proceed to any child
            # registration it needs to.
            child.parent = self
            child.root = self.root

# HINT: RootTask instance tracking code
# import weakref
# ROOTS = weakref.WeakSet()


class RootTask(ComplexTask):
    """Special task which is always the root of a measurement.

    On this class and this class only perform can and should be called
    directly.

    """
    #: Path to which log infos, preferences, etc should be written by default.
    default_path = Str('').tag(pref=True)

    #: Should the execution be profiled.
    should_profile = Bool().tag(pref=True)

    #: Dict storing data needed at execution time (ex: drivers classes)
    run_time = Dict()

    #: Inter-process event signaling the task it should stop execution.
    should_stop = Typed(Event)

    #: Inter-process event signaling the task it should pause execution.
    should_pause = Typed(Event)

    #: Inter-process event signaling the task is paused.
    paused = Typed(Event)

    #: Inter-process event signaling the main thread is done, handling the
    #: measurement resuming, and hence notifying the task execution has
    #: resumed.
    resumed = Typed(Event)

    #: Dictionary used to store errors occuring during performing.
    errors = Dict()

    #: Dictionary used to store references to resources that may need to be
    #: shared between task and which must be released when all tasks have been
    #: performed.
    #: Each key is associated to a different kind of resource. Resources must
    #: be stored in SharedDict subclass.
    #: By default three kind of resources exists:
    #:
    #: - threads : used threads grouped by pool.
    #: - active_threads : currently active threads.
    #: - instrs : used instruments referenced by profiles.
    #: - files : currently opened files by path.
    #:
    resources = Dict()

    #: Counter keeping track of the active threads.
    active_threads_counter = Typed(SharedCounter, kwargs={'count': 1})

    #: Counter keeping track of the paused threads.
    paused_threads_counter = Typed(SharedCounter, ())

    #: Thread from which the perform method has been called.
    thread_id = Int()

    # Those must not be modified so freeze them
    name = Constant('Root')
    depth = Constant(0)
    path = Constant('root')
    database_entries = set_default({'default_path': ''})

# HINT: RootTask instance tracking code
#    __slots__ = ('__weakref__',)

    def __init__(self, *args, **kwargs):
        self.preferences = ConfigObj(indent_type='    ', encoding='utf-8')
        self.database = TaskDatabase()
        super(RootTask, self).__init__(*args, **kwargs)
        self.register_in_database()
        self.root = self
        self.parent = self
        self.active_threads_counter.observe('count', self._state)
        self.paused_threads_counter.observe('count', self._state)

# HINT: RootTask instance tracking code
#        ROOTS.add(self)
#        print(len(ROOTS))

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
        """Run sequentially all child tasks, and close ressources.

        """
        result = True
        self.thread_id = threading.current_thread().ident

        self.prepare()

        pr = Profile() if self.should_profile else None

        try:
            if pr:
                pr.enable()
            for child in self.children:
                child.perform_()
        except Exception:
            log = logging.getLogger(__name__)
            msg = 'The following unhandled exception occured :\n'
            log.exception(msg)
            self.should_stop.set()
            result = False
            self.errors['unhandled'] = msg + format_exc()
        finally:
            if pr:
                pr.disable()
                meas_name = self.get_from_database('meas_name')
                meas_id = self.get_from_database('meas_id')
                path = os.path.join(self.default_path,
                                    meas_name + '_' + meas_id + '.prof')
                pr.dump_stats(path)
            self.release_resources()

        if self.should_stop.is_set():
            result = False

        return result

    def prepare(self):
        """Optimise the database for running state and prepare children.

        """
        # We cannot assume that the checks were run (in the case of a
        # forced-enqueueing) so we need to make sure we set the default path.
        self.write_in_database('default_path', self.default_path)
        self.database.prepare_to_run()
        super().prepare()

    def release_resources(self):
        """Release all the resources used by tasks.

        """
        # Release by priority to be sure that their is no-conflict
        # (Threads vs instruments for example)
        for resource in sorted(self.resources.values(),
                               key=attrgetter('priority')):
            resource.release()

    def register_in_database(self):
        """Don't create a node for the root task.

        """
        BaseTask.register_in_database(self)

        # ComplexTask defines children so we always get something
        for child in self.gather_children():
            child.register_in_database()

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
        task : RootTask
            Newly created and initiliazed task.

        Notes
        -----
        This method is fairly powerful and can handle a lot of cases so
        don't override it without checking that it works.

        """
        task = super(RootTask, cls).build_from_config(config, dependencies)
        task._post_setattr_root(None, task)
        task.register_in_database()
        task.register_preferences()
        return task

    def get_used_names(self):
        """Return the list of all names used in the tree
        Returns
        -------
        names : List(str)
            List of all the names used in the tree.

        """
        names = []
        for i in self.traverse():
            # Effectively ignores TaskInterface objects
            if hasattr(i, 'name'):
                names.append(i.name)
        return names

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    def _default_task_id(self):
        pack, _ = self.__module__.split('.', 1)
        return pack + '.' + ComplexTask.__name__

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
                # Reduce priority to stop through the thread resource.
                # This is far less likely to cause a deadlock.
                'active_threads': ThreadPoolResource(priority=0),
                'instrs': InstrsResource(),
                'files': FilesResource()}
