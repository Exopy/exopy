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
from threading import Thread, current_thread
from traceback import format_exc


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

    update_wrapper(decorator, function_to_decorate)
    return decorator


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
    def wrapper(*args, **kwargs):
        """Wrap function to run wrapped function in a new thread.

        """
        obj = args[0]
        root = obj.root
        safe_perform = smooth_crash(perform)

        def thread_perform(task, *args, **kwargs):
            safe_perform(task, *args, **kwargs)
            task.root.active_threads_counter.decrement()

        thread = Thread(group=None,
                        target=thread_perform,
                        args=args,
                        kwargs=kwargs)

        pools = obj.root.resources['threads']

        with pools.safe_access(pool) as threads:
            threads.append(thread)

        root.active_threads_counter.increment()
        thread.start()

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
        def wrapper(obj, *args, **kwargs):
            """Wrap function to wait upon specified pools.

            """
            all_threads = obj.root.resources['threads']
            while True:
                threads = []
                # Get all the threads we should be waiting upon.
                with all_threads.locked():
                    for p in wait:
                        threads.extend(all_threads[p])

                # If there is none break. Use any as threads is an iterator.
                if not any(threads):
                    break

                # Else join them.
                for thread in threads:
                    thread.join()

                # Make sure nobody modify the pools and update them by removing
                # the references to the dead threads.
                with all_threads.locked():
                    for w in wait:
                        all_threads[w] = [t for t in all_threads[w]
                                          if t.is_alive()]

                # Start over till no thread remain in the pools in wait.

            return perform(obj, *args, **kwargs)

    elif no_wait:
        def wrapper(obj, *args, **kwargs):
            """Wrap function not waiting on specified pools.

            """
            all_threads = obj.root.resources['threads']
            with all_threads.locked():
                pools = [k for k in all_threads if k not in no_wait]

            while True:
                # Get all the threads we should be waiting upon.
                threads = []
                with all_threads.locked():
                    for p in pools:
                        threads.extend(all_threads[p])

                # If there is None break. Use any as threads is an iterator.
                if not any(threads):
                    break

                # Else join them.
                for thread in threads:
                    thread.join()

                # Make sure nobody modify the pools and update them by removing
                # the references to the dead threads.
                with all_threads.locked():
                    for p in pools:
                        all_threads[p] = [t for t in all_threads[p]
                                          if t.is_alive()]

                # Start over till no thread remain in the pool in wait.

            return perform(obj, *args, **kwargs)
    else:
        def wrapper(obj, *args, **kwargs):
            """Wrap funxtion waiting on all pool threads.

            """
            all_threads = obj.root.resources['threads']
            while True:
                threads = []
                with all_threads.locked():
                    # Get all the threads we should be waiting upon.
                    for p in all_threads:
                        threads.extend(all_threads[p])

                # If there is none break. Use any as threads is an iterator.
                if not any(threads):
                    break

                # Else join them.
                for thread in threads:
                    thread.join()

                # Make sure nobody modify the pools and update them by removing
                # the references to the dead threads.
                with all_threads.locked():
                    for p in all_threads:
                        all_threads[p] = [t for t in all_threads[p]
                                          if t.is_alive()]
            return perform(obj, *args, **kwargs)

    update_wrapper(wrapper, perform)

    return wrapper
