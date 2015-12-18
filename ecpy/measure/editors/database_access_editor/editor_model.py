# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Model driving the database exception editor.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import Atom, Typed, List, ForwardTyped, Signal, Dict

from ....tasks.api import RootTask, ComplexTask
from ....tasks.tools.database import DatabaseNode
from ....utils.container_change import ContainerChange
from ....utils.atom_util import tagged_members


class NodeModel(Atom):
    """Object representing the database node state linked to a ComplexTask

    """
    #: Reference to the task this node refers to.
    task = Typed(ComplexTask)

    #: Reference to editor model.
    editor = ForwardTyped(lambda: EditorModel)

    #: Database entries available on the node associated with the task.
    entries = List()

    #: Database exceptions present on the node.
    exceptions = List()

    #: Database entries for which an access exception exists
    has_exceptions = List()

    #: Reference to the node which a parent of this one.
    parent = ForwardTyped(lambda: NodeModel)

    #: Children nodes
    children = List()

    #: Notifier for changes to the children. Simply there to satisfy the
    #: TaskEditor used in the view.
    children_changed = Signal()

    def __init__(self, **kwargs):

        super(NodeModel, self).__init__(**kwargs)
        for m in tagged_members(self.task, 'child_notifier'):
            self.task.observe(m, self._react_to_task_children_event)

    def sort_nodes(self):
        """Sort the nodes according to the task order.

        """
        tasks = [t for t in self.task.gather_children()
                 if isinstance(t, ComplexTask)]
        self.children = sorted(self.children,
                               key=lambda n: tasks.index(n.task))

    def add_exception(self, entry):
        """Add an access exception.

        """
        task, entry = self._find_task_from_entry(entry)

        if entry not in task.access_exs:
            task.add_access_exception(entry, 1)

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    def _react_to_task_children_event(self, change):
        """Simply reorder the nodes if it was a move event.

        Only move events are transparent to the database.

        """
        if isinstance(change, ContainerChange):
            if change.collapsed:
                for c in change.collapsed:
                    self._react_to_task_children_event(c)

            if change.moved:
                self.sort_nodes()

    def _find_task_from_entry(self, full_entry):
        """Find the task and short name corresponding to a full entry name.

        """
        possible_tasks = [t for t in self.task.gather_children() if
                          full_entry.startswith(t.name)]
        if len(possible_tasks) > 1:
            for p in possible_tasks:
                e = full_entry[len(p.name)+1:]
                if e in p.database_entries:
                    break
            task = p
            entry = e
        else:
            task = possible_tasks[0]
            entry = full_entry[len(task.name)+1:]

        return task, entry


class EditorModel(Atom):
    """Model driving the database access editor.

    """
    #: Reference to the root task of the currently edited task hierarchy.
    root = Typed(RootTask)

    #: Signal that a node was deleted (the payload is the node model object).
    node_deleted = Signal()

    #: Dictionary storing the nodes for all tasks by path.
    nodes = Dict()

    def increase_exc_level(self, path, entry):
        """Increase the exception level of an access exception.

        Parameters
        ----------
        path : unicode
            Path of the node in which the exception to increase is.

        entry : unicode
            Entry whose access exception should be increased.

        """
        self._modify_exception_level(path, entry, 1)

    def decrease_exc_level(self, path, entry):
        """Decrease the exception level of an access exception.

        Parameters
        ----------
        path : unicode
            Path of the node in which the exception to increase is.

        entry : unicode
            Entry whose access exception should be increased.

        """
        self._modify_exception_level(path, entry, -1)

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    def _modify_exception_level(self, path, entry, val):
        """Modify the exception level of an access exception.

        Parameters
        ----------
        path : unicode
            Path of the node in which the exception to increase is.

        entry : unicode
            Entry whose access exception should be increased.

        val : int
            Amount by which to modify the level.

        """
        database_node = self.root.database.go_to_path(path)
        real_path = path + '/' + database_node.meta['access'][entry]
        task, entry = self.nodes[real_path]._find_task_from_entry(entry)
        level = task.access_exs[entry]
        task.modify_access_exception(entry, level + val)

    def _post_setattr_root(self, old, new):
        """Ensure we are observing the right database.

        """
        if old:
            old.database.unobserve('notifier', self._react_to_entries)
            old.database.unobserve('access_notifier',
                                   self._react_to_exceptions)
            old.database.unobserve('nodes_notifier', self._react_to_nodes)

        if new:
            new.database.observe('notifier', self._react_to_entries)
            new.database.observe('access_notifier', self._react_to_exceptions)
            new.database.observe('nodes_notifier', self._react_to_nodes)

            database_nodes = new.database.list_nodes()
            nodes = {p: self._model_from_node(p, n)
                     for p, n in database_nodes.items()}
            for p, m in nodes.items():
                if '/' in p:
                    p, _ = p.rsplit('/', 1)
                    m.parent = nodes[p]
                    nodes[p].children.append(m)

            for nmodel in nodes.values():
                nmodel.sort_nodes()

            self.nodes = nodes

    def _react_to_entries(self, news):
        """Handle modification to entries.

        """
        if isinstance(news, list):
            for n in news:
                self._react_to_entries(n)
            return

        path, entry = news[1].rsplit('/', 1)
        n = self.nodes[path]
        if news[0] == 'added':
            n.entries = n.entries[:] + [entry]

        elif news[0] == 'renamed':
            entries = n.entries[:]
            del entries[entries.index(entry)]
            entries.append(news[2].rsplit('/', 1)[1])
            n.entries = entries

        elif news[0] == 'removed':
            entries = n.entries[:]
            del entries[entries.index(entry)]
            n.entries = entries

    def _react_to_exceptions(self, news):
        """Handle modifications to the access exceptions.

        """
        if isinstance(news, list):
            for n in news:
                self._react_to_exceptions(n)
            return

        path = news[1]
        n = self.nodes[path]
        origin_node = self.nodes[path + '/' + news[2] if news[2] else path]
        if news[0] == 'added':
            n.exceptions = n.exceptions[:] + [news[3]]

            origin_node.has_exceptions = n.has_exceptions[:] + [news[3]]

        elif news[0] == 'renamed':
            exceptions = n.exceptions[:]
            del exceptions[exceptions.index(news[3])]
            exceptions.append(news[4])
            n.exceptions = exceptions

            exs = origin_node.has_exceptions[:]
            del exs[exs.index(news[3])]
            exs.append(news[4])
            origin_node.has_exceptions = exs

        elif news[0] == 'removed':
            exceptions = n.exceptions[:]
            if news[3]:
                del exceptions[exceptions.index(news[3])]
                n.exceptions = exceptions

                exs = origin_node.has_exceptions[:]
                del exs[exs.index(news[3])]
                origin_node.has_exceptions = exs
            else:
                n.exceptions = []
                origin_node.has_exceptions = []

    def _react_to_nodes(self, news):
        """Handle modifications of the database nodes.

        """
        if isinstance(news, list):
            for n in news:
                self._react_to_nodes(n)
            return

        path = news[1] + '/' + news[2]
        if news[0] == 'added':
            parent = self.nodes[news[1]]
            model = self._model_from_node(path, news[3])
            model.parent = parent
            parent.children.append(model)
            parent.sort_nodes()
            self.nodes[path] = model

        elif news[0] == 'renamed':
            new_path = news[1] + '/' + news[3]
            nodes = self.nodes.copy()
            for k, v in nodes.items():
                if k.startswith(path):
                    del self.nodes[k]
                    self.nodes[new_path + k[len(path):]] = v

        elif news[0] == 'removed':
            node = self.nodes[path]
            del self.nodes[path]
            parent = node.parent
            del parent.children[parent.children.index(node)]
            parent.sort_nodes()
            self.node_deleted(node)

    def _get_task(self, path):
        """Retrieve the task corresponding to a certain path.

        """
        if '/' not in path:
            return self.root

        names = path.split('/')[1:]
        task = self.root
        for n in names:
            for t in task.gather_children() + [None]:
                if t is None:
                    raise ValueError('No task matching the specified path')
                if t.name == n:
                    task = t
                    break

        return task

    def _model_from_node(self, path, node):
        """Build a new model from a node informations.

        """
        entries = [k for k, v in node.data.items()
                   if not isinstance(v, DatabaseNode)]
        excs = list(node.meta.get('access', {}).keys())
        return NodeModel(editor=self, entries=entries,
                         exceptions=excs, task=self._get_task(path))
