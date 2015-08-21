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

from atom.api import Atom, Typed, List, ForwardTyped, Signal, Dict, Unicode

from ....tasks.api import RootTask, ComplexTask
from ....tasks.tools.database import DatabaseNode
from ....utils.container_change import ContainerChange
from ....utils.atom_util import tagged_members


class NodeModel(Atom):
    """Object representing the database node state linked to a ComplexTask

    """
    #: Reference to the task this node refers to.
    task = Unicode()

    #: Reference to editor model.
    editor = ForwardTyped(lambda: EditorModel)

    #: Database entries available on the node associated with the task.
    entries = List()

    #: Database exceptions present on the node.
    exceptions = List()

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
        tasks = filter(lambda t: isinstance(t, ComplexTask),
                       self.task.gather_children())
        self.children = sorted(self.children, lambda n: tasks.index(n.task))

    def add_exception(self, entry):
        """Add an access exception

        """
        entry = entry[len(self.task.name)+1:]
        self.task.add_access_exception(entry, 1)

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
        real_path = database_node.meta.access[entry]
        task = self._get_task(real_path)
        entry = entry[len(task.name)+1:]
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

            nodes = {}
            for p, n in new.database.list_nodes():
                model = self._model_from_node(p, n)
                nodes[p] = model

                if '/' in p:
                    p, _ = p.rsplit('/', 1)
                    if p in nodes:
                        model.parent = nodes[p]
                        nodes[p].children.append(model)

            for nmodel in nodes.values():
                nmodel.sort_nodes()

            self.nodes = nodes

    def _react_to_entries(self, news):
        """Handle modification to entries.

        """
        path, entry = news[1].rsplit('/', 1)
        n = self.nodes[path]
        if news[0] == 'added':
            n.entries = n.entries[:] + [entry]

        elif news[0] == 'renamed':
            entries = n.entries[:]
            del entries[entries.index(entry)]
            entries.append(news[2].rsplit('/', 1)[1])
            n.entries = entries

        elif news == 'removed':
            entries = n.entries[:]
            del entries[entries.index(entry)]
            n.entries = entries

    def _react_to_exceptions(self, news):
        """Handle modifications to the access exceptions.

        """
        path = news[1]
        n = self.nodes[path]
        if news[0] == 'added':
            n.exceptions = n.exceptions[:] + [news[2]]

        elif news[0] == 'renamed':
            exceptions = n.exceptions[:]
            del exceptions[exceptions.index(news[2])]
            exceptions.append(news[3])
            n.exceptions = exceptions

        elif news == 'removed':
            exceptions = n.exceptions[:]
            del exceptions[exceptions.index(news[2])]
            n.exceptions = exceptions

    def _react_to_nodes(self, news):
        """Handle modifications of the database nodes.

        """
        path = news[1] + '/' + news[2]
        if news[0] == 'added':
            parent = self.nodes[news[1]]
            model = self._model_from_node(path, news[3])
            model.parent = parent
            parent.children.append(NodeModel())
            parent.sort_nodes()

        elif news[0] == 'renamed':
            node = self.nodes[path]
            node.path = news[1] + '/' + news[3]

        elif news == 'removed':
            node = self.nodes[path]
            del self.nodes[path]
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
        return NodeModel(editor=self, path=path, entries=entries,
                         exceptions=excs, task=self._get_task(path))
