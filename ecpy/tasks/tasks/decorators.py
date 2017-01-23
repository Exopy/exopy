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

import logging
from functools import update_wrapper
from time import sleep
from threading import Thread, Event, current_thread
from traceback import format_exc

from atom.api import Atom, Value, Callable, Unicode


def handle_stop_pause(root):
    """Check the state of the stop and pause event and handle the pause.

    When the pause stops the main thread take care of re-initializing the
    driver owners (so that any user modification shoudl not cause a crash) and
    signal the other threads it is done by setting the resume flag.

    Parameters
    ----------
    root : RootTask
        RootTask of the hierarchy.

    Returns
    -------
    exit : bool or None
        Whether or not the function returned because should_stop was set.

    """
    stop_flag = root.should_stop
    if stop_flag.is_set():
        return True

    pause_flag = root.should_pause
    if pause_flag.is_set():
        root.resumed.clear()
        root.paused_threads_counter.increment()
        while True:
            sleep(0.05)
            if stop_flag.is_set():
                root.paused_threads_counter.decrement()
                return True
            if not pause_flag.is_set():
                if current_thread().ident == root.thread_id:
                    # Prevent issues if a user alter a resource while in pause.
                    for _, resource in root.resources.items():
                        resource.reset()
                    root.resumed.set()
                    root.paused_threads_counter.decrement()
                    break
                else:
                    # Safety here ensuring the main thread finished
                    # re-initializing the resources.
                    root.resumed.wait()
                    root.paused_threads_counter.decrement()
                    break


def make_stoppable(function_to_decorate):
    """Decorator allowing to stop or pause at the beginning of a task.

    This is applied the perform method of every task marked as stoppable. This
    check is performed before dealing with parallelism or waiting.

    """
    def decorator(*args, **kwargs):
        """Wrap function to check for stop/pause condition.

        """
        if handle_stop_pause(args[0].root):
            return

        return function_to_decorate(*args, **kwargs)

    update_wrapper(decorator, function_to_decorate)

    return decorator


def smooth_crash(function_to_decorate):
    """This decorator ensures that any unhandled error will cause the measure
    to stop in a nice way. It is always present at the root call of any thread.

    """
    def decorator(*args, **kwargs):
        """Wrap function to handle nicelay craches.

        """
        obj = args[0]

        try:
            return function_to_decorate(*args, **kwargs)
        except Exception:
            log = logging.getLogger(function_to_decorate.__module__)
            msg = 'The following unhandled exception occured in %s :'
            log.exception(msg % obj.name)
            obj.root.should_stop.set()
            obj.root.errors['unhandled'] = msg % obj.name + '\n' + format_exc()
            return False

    update_wrapper(decorator, function_to_decorate)
    return decorator


class ThreadDispatcher(Atom):
    """Dispatch calling a function to a thread.

    """

    #: Flag set when the thread is ready to accept new jobs.
    inactive = Value(factory=Event)

    def __init__(self, perform, pool):
        self._func = smooth_crash(perform)
        self._pool = pool
        self.inactive.set()

    def dispatch(self, task, *args, **kwargs):
        """Dispatch the work to the background thread.

        """
        if self._thread is None:
            pools = task.root.resources['threads']
            with pools.safe_access(self._pool) as threads:
                threads.append(self)
            self._thread = Thread(group=None,
                                  target=self._background_loop)
            self._thread.start()

        # Make sure the background thread is done processing the previous work.
        self.inactive.wait()

        # Mark the thread as active.
        self.inactive.clear()
        task.root.active_threads_counter.increment()
        pools = task.root.resources['active_threads']
        with pools.safe_access(self._pool) as threads:
            threads.append(self)

        # Pass the arguments
        self._args_kwargs = task, args, kwargs
        self._new_args.set()

    def stop(self):
        """Stop the background thread.

        """
        if self._thread is None:
            return

        while self._new_args.is_set():
            sleep(1e-3)
        self.inactive.wait()
        self._args_kwargs = (None, None, None)
        self._new_args.set()
        self._thread.join()
        del self._thread
        self.inactive.set()

    # --- Private API ---------------------------------------------------------

    #: Thread to which the work is dispatched.
    _thread = Value()

    #: Flag set when the new arguments are available..
    _new_args = Value(factory=Event)

    #: Arguments and keywords arguments for the next dispatch.
    _args_kwargs = Value()

    #: Reference to the function to call on each dispatch.
    _func = Callable()

    #: Pool id to which this dispatcher belongs.
    _pool = Unicode()

    def _background_loop(self):
        """Background function executed by the thread.

        """
        while True:
            self._new_args.wait()
            task, args, kwargs = self._args_kwargs
            if task is None:
                break
            self._func(task, *args, **kwargs)
            self._new_args.clear()
            self.inactive.set()
            task.root.active_threads_counter.decrement()


def make_parallel(perform, pool):
    """Machinery to execute perform in parallel.

    Create a wrapper around a method to execute it in a thread and register the
    thread.

    Parameters
    ----------
    perform : method
        Method which should be wrapped to run in parallel.

    pool : str
        Name of the execution pool to which the created thread belongs.

    """
    dispatcher = ThreadDispatcher(perform, pool)

    def wrapper(*args, **kwargs):
        return dispatcher.dispatch(*args, **kwargs)

    update_wrapper(wrapper, perform)
    return wrapper


def make_wait(perform, wait, no_wait):
    """Machinery to make perform wait on other tasks execution.

    Create a wrapper around a method to wait for some threads to terminate
    before calling the method. Threads are grouped in execution pools.
    This method supports new threads being started while it is waiting.

    Parameters
    ----------
    perform : method
        Method which should be wrapped to wait on threads.

    wait : list(str)
        Names of the execution pool which should be waited for.

    no_wait : list(str)
        Names of the execution pools which should not be waited for.

    Both parameters are mutually exlusive. If both lists are empty the
    execution will be deffered till all the execution pools have completed
    their works.

    """
    if wait:
        def get_pools(active_threads):
            """Get the pools on which to wait.

            """
            return wait

    elif no_wait:
        def get_pools(active_threads):
            """Get the pools on which to wait.

            """
            with active_threads.locked():
                pools = [k for k in active_threads if k not in no_wait]
            return pools

    else:
        def get_pools(active_threads):
            """Get the pools on which to wait.

            """
            return list(active_threads)

    def wrapper(obj, *args, **kwargs):
        """Wrap function to wait upon specified pools.

        """
        all_threads = obj.root.resources['active_threads']
        while True:
            threads = []
            # Get all the pools we should be operating on.
            pools = get_pools(all_threads)

            # Get all the threads we should be operating upon.
            with all_threads.locked():
                for p in pools:
                    threads.extend(all_threads[p])

            # If there is none break. Use any as threads is an iterator.
            if not any(threads):
                break

            # Else join them.
            for thread in threads:
                thread.inactive.wait()

            # Make sure nobody modify the pools and update them by removing
            # the references to the dead threads.
            with all_threads.locked():
                for p in pools:
                    all_threads[p] = [t for t in all_threads[p]
                                      if not t.inactive.is_set()]

            # Start over till no thread remain in the pools in wait.

        return perform(obj, *args, **kwargs)

    update_wrapper(wrapper, perform)

    return wrapper
