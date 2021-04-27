# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Model for the execution editor keeping track of the declared pools.

"""
from collections import Counter
from collections.abc import Iterable

from atom.api import Atom, Value, Typed, List

from ....tasks.api import ComplexTask
from ....utils.atom_util import tagged_members


class ExecutionEditorModel(Atom):
    """Model for the execution editor.

    Walk all the tasks to determine which pool of tasks are defined and keep a
    counter.

    """
    #: Reference to the root task of the hierarchy.
    root = Value()

    #: List of already existing execution pools.
    pools = List()

    def bind_observers(self):
        """Set up the observers on the task hierarchy.

        """
        counter = Counter()
        self._bind_observers(self.root, counter)

        self._counter = counter
        self.pools = list(set(counter.elements()))

    def unbind_observers(self):
        """Remove all the observer from all tasks.

        """
        self._unbind_observers(self.root, Counter())

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

    #: Counter keeping track of how many times each pool appear.
    _counter = Typed(Counter, ())

    def _bind_observers(self, task, counter):
        """Bind the observer to a specific task and its children.

        """
        if isinstance(task, ComplexTask):
            for m in tagged_members(task, 'child'):
                task.observe(m, self._child_observer)
            for m in tagged_members(task, 'child_notifier'):
                task.observe(m, self._child_notifier_observer)
            for child in task.gather_children():
                self._bind_observers(child, counter)

        pools = []
        parallel = task.parallel
        if parallel.get('activated'):
            pool = parallel['pool']
            if pool:
                pools.append(pool)

        wait = task.wait
        if wait.get('activated'):
            pools.extend(wait.get('wait', []))
            pools.extend(wait.get('no_wait', []))

        counter.update(pools)

        task.observe('parallel', self._task_observer)
        task.observe('wait', self._task_observer)

    def _unbind_observers(self, task, counter):
        """Remove the observer linked to a specific task.

        """
        if isinstance(task, ComplexTask):
            for m in tagged_members(task, 'child'):
                task.unobserve(m, self._child_observer)
            for m in tagged_members(task, 'child_notifier'):
                task.unobserve(m, self._child_notifier_observer)
            for child in task.gather_children():
                self._unbind_observers(child, counter)

        pools = []
        parallel = task.parallel
        if parallel.get('activated'):
            pool = parallel['pool']
            if pool:
                pools.append(pool)

        wait = task.wait
        if wait.get('activated'):
            pools.extend(wait.get('wait', []))
            pools.extend(wait.get('no_wait', []))

        counter.subtract(pools)

        task.unobserve('parallel', self._task_observer)
        task.unobserve('wait', self._task_observer)

    def _post_setattr_root(self, old, new):
        """Make sure we always observe the right root.

        """
        if old:
            self._unbind_observers(old, self._counter)

        if new:
            self.bind_observers()

    def _task_observer(self, change):
        """Observer handler reacting to task change.

        """
        if change['name'] == 'parallel':
            activated = change['value'].get('activated')
            pool = change['value'].get('pool')
            if not activated and pool:
                self._counter[pool] -= 1

            elif activated and pool:
                self._counter[pool] += 1

            self._update_pools()

        else:
            activated = change['value'].get('activated')
            wait = change['value'].get('wait', [])
            no_wait = change['value'].get('no_wait', [])
            counter = Counter(wait + no_wait)

            if not activated and counter:
                self._counter.subtract(counter)

            elif activated and counter:
                self._counter.update(counter)

            self._update_pools()

    def _child_observer(self, change):
        """Observe rtracking a member tagged with child.

        """
        counter = Counter()
        value = change['value']
        if isinstance(value, Iterable):
            for c in value:
                self._bind_observers(c, counter)
        elif value:
            self._bind_observers(value, counter)

        if 'oldvalue' in change:
            value = change['oldvalue']
            if isinstance(value, Iterable):
                for c in value:
                    self._unbind_observers(c, counter)
            elif value:
                self._unbind_observers(value, counter)

        self._counter.update(counter)
        self._update_pools()

    def _child_notifier_observer(self, change):
        """Keep track of children addition and removal.

        """
        if change.collapsed:
            for c in change.collapsed:
                self._child_notifier_observer(c)

        counter = Counter()

        for _, child in change.removed:
            self._unbind_observers(child, counter)

        for _, child in change.added:
            self._bind_observers(child, counter)

        self._counter.update(counter)
        self._update_pools()

    def _update_pools(self, counter=None):
        """Update the pool with the elements having a positive count.

        """
        c = counter or self._counter
        self.pools = list(set(c.elements()))
