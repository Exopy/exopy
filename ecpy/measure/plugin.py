# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Plugin handling all measure related functions.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import logging
import os
from time import sleep
from collections import Iterable
from inspect import cleandoc
from functools import partial
from enum import IntEnum

import enaml
from atom.api import Typed, Unicode, List, ForwardTyped, Int, Enum, Signal

from ..utils.container_change import ContainerChange
from ..utils.plugin_tools import (HasPrefPlugin, ExtensionsCollector,
                                  make_extension_validator)
from .engines import BaseEngine, Engine
from .monitors import Monitor
from .hooks import PreExecutionHook, PostExecutionHook
from .editors import Editor
from .measure import Measure

logger = logging.getLogger(__name__)

INVALID_MEASURE_STATUS = ['EDITING', 'SKIPPED', 'FAILED', 'COMPLETED',
                          'INTERRUPTED']

ENGINES_POINT = 'ecpy.measure.engines'

MONITORS_POINT = 'ecpy.measure.monitors'

PRE_HOOK_POINT = 'ecpy.measure.pre-execution'

POST_HOOK_POINT = 'ecpy.measure.post-execution'

EDITORS_POINT = 'ecpy.measure.editors'


class MeasureFlags(IntEnum):
    """Enumeration defining the bit flags used by the measure plugin.

    """
    processing = 1
    stop_attempt = 2
    stop_processing = 4
    no_post_exec = 8


def _workspace():
    from .workspace import MeasureSpace
    return MeasureSpace


class MeasurePlugin(HasPrefPlugin):
    """The measure plugin is reponsible for managing all measure related
    extensions and handling measure execution.

    """
    #: Reference to the workspace if any.
    workspace = ForwardTyped(_workspace)

    #: Reference to the last path used to load a measure
    path = Unicode().tag(pref=True)

    #: Currently edited measures. The list should not be manipulated
    #: directly by user code. Use the edd/move/remove_measure functions.
    edited_measures = List()

    #: Signal emitted whenever a measure is added or removed from the list of
    #: edited measures, the payload will be a ContainerChange instance.
    edited_measures_changed = Signal()

    #: Currently enqueued measures. The list should not be manipulated
    #: directly by user code. Use the edd/move/remove_measure functions.
    enqueued_measures = List()

    #: Signal emitted whenever a measure is added or removed from the list of
    #: enqueued measures, the payload will be a ContainerChange instance.
    enqueued_measures_changed = Signal()

    #: Currently run measure or last measure run.
    running_measure = Typed(Measure)

    #: List of currently available engines.
    engines = List()

    #: Currently selected engine represented by its id.
    selected_engine = Unicode().tag(pref=True)

    #: Instance of the currently used engine.
    engine_instance = Typed(BaseEngine)

    #: What to do of the engine when there is no more measure to perform.
    engine_policy = Enum('stop', 'sleep').tag(pref=True)

    #: List of currently available pre-execution hooks.
    pre_hooks = List()

    #: Default pre-execution hooks to use for new measures.
    default_pre_hooks = List().tag(pref=True)

    #: List of currently available monitors.
    monitors = List()

    #: Default monitors to use for new measures.
    default_monitors = List().tag(pref=True)

    #: List of currently available post-execution hooks.
    post_hooks = List()

    #: Default post-execution hooks to use for new measures.
    default_hooks = List().tag(pref=True)

    #: Dict holding the contributed Editor declarations
    editors = List()

    # Internal flags used to keep track of the execution state.
    flags = Int()

    def start(self):
        """Start the plugin lifecycle by collecting all contributions.

        """
        super(MeasurePlugin, self).start()
        if not os.path.isdir(self.path):
            self.path = ''

        checker = make_extension_validator(Engine, ('new',))
        self._engines = ExtensionsCollector(workbench=self.workbench,
                                            point=ENGINES_POINT,
                                            ext_class=Engine,
                                            validate_ext=checker)
        self._engines.start()

        checker = make_extension_validator(Editor, ('new', 'is_meant_for'))
        self._editors = ExtensionsCollector(workbench=self.workbench,
                                            point=EDITORS_POINT,
                                            ext_class=Editor,
                                            validate_ext=checker)
        self._editors.start()

        checker = make_extension_validator(PreExecutionHook,  ('new',))
        self._pre_hooks = ExtensionsCollector(workbench=self.workbench,
                                              point=PRE_HOOK_POINT,
                                              ext_class=PreExecutionHook,
                                              validate_ext=checker)
        self._pre_hooks.start()

        checker = make_extension_validator(Monitor, ('new',))
        self._monitors = ExtensionsCollector(workbench=self.workbench,
                                             point=MONITORS_POINT,
                                             ext_class=Monitor,
                                             validate_ext=checker)
        self._monitors.start()

        checker = make_extension_validator(PostExecutionHook, ('new',))
        self._post_hooks = ExtensionsCollector(workbench=self.workbench,
                                               point=POST_HOOK_POINT,
                                               ext_class=PostExecutionHook,
                                               validate_ext=checker)
        self._post_hooks.start()

        for contrib in ('engines', 'editors', 'pre_hooks', 'monitors',
                        'post_hooks'):
            self._update_contribs(contrib, None)
            if contrib not in ('engines', 'editors'):
                default = getattr(self, 'default_'+contrib)
                avai_default = [d for d in default
                                if d in getattr(self, contrib)]
                if default != avai_default:
                    msg = 'The following {}s have not been found : {}'
                    missing = set(default) - set(avai_default)
                    logger.info(msg.format(contrib, missing))
                    setattr(self, 'default_'+contrib, avai_default)
            getattr(self, '-'+contrib).observe('contributions',
                                               partial(self._update_contribs,
                                                       contrib))

    def stop(self):
        """Stop the plugin and remove all observers.

        """
        for contrib in ('engines', 'editors', 'pre_hooks', 'monitors',
                        'post_hooks'):
            getattr(self, '-'+contrib).stop()

    def get_declarations(self, kind, ids):
        """Get the declarations of engines/editors/tools

        Parameters
        ----------
        kind : {'engine', 'editor', 'pre-hook', 'monitor', 'post-hook'}
            Kind of object to create.

        ids : list
            Ids of the declarations to return.

        Returns
        -------
        declarations : dict
            Declarations stored in a dict by id.

        """
        kinds = ('engine', 'editor', 'pre-hook', 'monitor', 'post-hook')
        if kind not in kinds:
            msg = 'Expected kind must be one of {}, not {}.'
            raise ValueError(msg.format(kinds, kind))

        decls = getattr(self, '_'+kind+'s').contributions
        return {k: v for k, v in decls.iteritems() if k in ids}

    def create(self, kind, id, default=True):
        """Create a new instance of an engine/editor/tool.

        Parameters
        ----------
        kind : {'engine', 'editor', 'pre-hook', 'monitor', 'post-hook'}
            Kind of object to create.

        id : unicode
            Id of the object to create.

        default : bool, optional
            Whether to use default parameters or not when creating the object.

        Returns
        -------
        obj :
            New instance of the requested object.

        Raises
        ------
        ValueError :
            Raised if the provided kind or id in incorrect.

        """
        kinds = ('engine', 'editor', 'pre-hook', 'monitor', 'post-hook')
        if kind not in kinds:
            msg = 'Expected kind must be one of {}, not {}.'
            raise ValueError(msg.format(kinds, kind))

        decls = getattr(self, '_'+kind+'s').contributions
        if id not in decls:
            raise ValueError('Unknown {} : {}'.format(kind, id))

        return decls[id].new(self.workbench, default)

    def add_measure(self, kind, measure, index=None):
        """Add a measure to the edited or enqueued ones.

        Parameters
        ----------
        kind : unicode, {'edited', 'enqueued'}
            Is this measure to be added to the enqueued or edited ones.

        measure : Measure
            Measure to add.

        index : int | None
            Index at which to insert the measure. If None the measure is
            appended.

        """
        name = kind+'_measures'
        measures = getattr(self, name)
        notification = ContainerChange(obj=self, name=name)
        if index is None:
            measures.append(measure)
            index = measures.index(measure)
        else:
            measures.insert(index, measure)

        notification.add_operation('added', (index, measure))
        signal = getattr(self, kind+'_measures_changed')
        signal(notification)

    def move_measure(self, kind, old, new):
        """Move a measure.

        Parameters
        ----------
        kind : unicode, {'edited', 'enqueued'}
            Is this measure to be added to the enqueued or edited ones.

        old : int
            Index at which the measure to move currently is.

        new_position : int
            Index at which to insert the measure.

        """
        name = kind+'_measures'
        measures = getattr(self, name)
        measure = measures[old]
        del measures[old]
        measures.insert(new, measure)

        notification = ContainerChange(obj=self, name=name)
        notification.add_operation('moved', (old, new, measure))
        signal = getattr(self, kind+'_measures_changed')
        signal(notification)

    def remove_measures(self, kind, measures):
        """Remove a measure or a list of measure.

        Parameters
        ----------
        kind : unicode, {'edited', 'enqueued'}
            Is this measure to be added to the enqueued or edited ones.

        measures : Measure|list[Measure]
            Measure(s) to remove.

        """
        name = kind+'_measures'
        measures = getattr(self, name)

        if not isinstance(measures, Iterable):
            measures = [measures]

        notification = ContainerChange(obj=self, name=name)
        for measure in measures:
            old = measures.index(measure)
            del measures[old]
            notification.add_operation('removed', (old, measure))

        signal = getattr(self, kind+'_measures_changed')
        signal(notification)

    def start_measure(self, measure):
        """Start a new measure.

        """
        logger = logging.getLogger(__name__)

        # Discard old monitors if there is any remaining.
        if self.running_measure:
            for monitor in self.running_measure.monitors.values():
                monitor.stop()

        measure.enter_running_state()
        self.running_measure = measure

        self.flags |= MeasureFlags.processing

        core = self.workbench.get_plugin('enaml.workbench.core')

        # Checking build dependencies, if present simply request runtimes.
        if 'build_deps' in measure.store and 'runtime_deps' in measure.store:
            # Requesting runtime, so that we get permissions.

            runtimes = measure.store['runtime_deps']
            cmd = 'ecpy.app.dependencies.request_runtimes'
            deps = core.invoke_command(cmd,
                                       {'obj': measure.root_task,
                                        'owner': [self.manifest.id],
                                        'dependencies': runtimes},
                                       )
            res = self.check_for_dependencies_errors(measure, deps, skip=True)
            if not res:
                return

        else:
            # Collect build and runtime dependencies.
            cmd = 'ecpy.app.dependencies.collect'
            b_deps, r_deps = core.invoke_command(cmd,
                                                 {'obj': measure.root_task,
                                                  'dependencies': ['build',
                                                                   'runtime'],
                                                  'owner': self.manifest.id})

            res = self.check_for_dependencies_errors(measure, b_deps,
                                                     skip=True)
            res &= self.check_for_dependencies_errors(measure, r_deps,
                                                      skip=True)
            if not res:
                return

        # Records that we got access to all the runtimes.
        mess = cleandoc('''The use of all runtime resources have been
                        granted to the measure %s''' % measure.name)
        logger.info(mess.replace('\n', ' '))

        # Run checks now that we have all the runtimes.
        res, errors = measure.run_checks(self.workbench)
        if not res:
            cmd = 'ecpy.app.errors.signal'
            msg = 'Measure %s failed to pass the checks.' % measure.name
            core.invoke_command(cmd, {'kind': 'measure-error',
                                      'message': msg % (measure.name),
                                      'errors': errors})

            self._skip_measure('FAILED', 'Failed to pass the checks')
            return

        # Now that we know the measure is going to run save it.
        default_filename = measure.name + '_' + measure.id + '.meas.ini'
        path = os.path.join(measure.root_task.default_path, default_filename)
        measure.save(path)

        # Start the engine if it has not already been done.
        if not self.engine_instance:
            decl = self.engines[self.selected_engine]
            engine = decl.factory(decl, self.workbench)
            self.engine_instance = engine

            # Connect signal handler to engine.
            engine.observe('completed', self._listen_to_engine)

        engine = self.engine_instance

        # Call engine prepare to run method.
        engine.prepare_to_run(measure)

        # Execute all pre-execution hook.
        measure.run_pre_execution()

        # Get a ref to the main window.
        ui_plugin = self.workbench.get_plugin('enaml.workbench.ui')
        # Connect new monitors, and start them.
        for monitor in measure.monitors.values():
            engine.observe('news', monitor.process_news)
            monitor.start(ui_plugin.window)

        logger.info('''Starting measure {}.'''.format(measure.name))
        # Ask the engine to start the measure.
        engine.run()

    def pause_measure(self):
        """Pause the currently active measure.

        """
        logger.info('Pausing measure {}.'.format(self.running_measure.name))
        self.engine_instance.pause()

    def resume_measure(self):
        """Resume the currently paused measure.

        """
        logger.info('Resuming measure {}.'.format(self.running_measure.name))
        self.engine_instance.resume()

    def stop_measure(self, no_post_exec=False):
        """Stop the currently active measure.

        """
        logger.info('Stopping measure {}.'.format(self.running_measure.name))
        self.flags |= MeasureFlags.stop_attempt
        if no_post_exec:
            self.flags |= MeasureFlags.no_post_exec
        self.engine_instance.stop()

    def stop_processing(self, no_post_exec=False):
        """Stop processing the enqueued measure.

        """
        logger.info('Stopping measure {}.'.format(self.running_measure.name))
        self.flags |= MeasureFlags.stop_attempt | MeasureFlags.stop_processing
        if self.flags and MeasureFlags.processing:
            self.flags &= ~MeasureFlags.processing
        if no_post_exec:
            self.flags |= MeasureFlags.no_post_exec
        self.engine_instance.exit()

    def force_stop_measure(self):
        """Force the engine to stop performing the current measure.

        """
        logger.info('Exiting measure {}.'.format(self.running_measure.name))
        self.flags |= MeasureFlags.no_post_exec
        self.engine_instance.force_stop()

    def force_stop_processing(self):
        """Force the engine to exit and stop processing measures.

        """
        logger.info('Exiting measure {}.'.format(self.running_measure.name))
        self.flags |= MeasureFlags.stop_processing | MeasureFlags.no_post_exec
        if self.flags & MeasureFlags.processing:
            self.flags &= ~MeasureFlags.processing
        self.engine_instance.force_exit()

    def find_next_measure(self):
        """Find the next runnable measure in the queue.

        Returns
        -------
        measure : Measure
            First valid measurement in the queue or None if there is no
            available measure.

        """
        enqueued_measures = self.enqueued_measures
        i = 0
        measure = None
        # Look for a measure not being currently edited. (Can happen if the
        # user is editing the second measure when the first measure ends).
        while i < len(enqueued_measures):
            measure = enqueued_measures[i]
            if measure.status in INVALID_MEASURE_STATUS:
                i += 1
                measure = None
            else:
                break

        return measure

    def check_for_dependencies_errors(self, measure, deps, skip=False):
        """Check that the collection of dependencies occurred without errors.

        Parameters
        ----------
        measure : Measure
            Measure whose dependencies have been collected.

        deps : BuildContainer, RuntimeContainer
            Dependencies container.

        skip : bool
            Should an error trigger a false engine event marking the measure
            as failed or skipped.

        Returns
        -------
        result : bool
            Boolean indicating if everything was ok or not.

        """
        core = self.workbench.get_plugin('enaml.workbench.core')
        kind = 'runtime' if hasattr(deps, 'unavailable') else 'build'
        cmd = 'ecpy.app.errors.signal'
        if deps.errors:
            msg = 'Failed to get some %s dependencies for measure %s'
            core.invoke_command(cmd, {'kind': 'measure-error',
                                      'message': msg % (kind, measure.name),
                                      'errors': deps.errors})
            if skip:
                self._skip_measure('FAILED',
                                   'Failed to get some %s dependencies' % kind)
            return False

        if getattr(deps, 'unavailable', None):
            msg = ('The following runtime dependencies of measure %s are '
                   'unavailable :\n')
            msg += '\n'.join('- %s' % u for u in deps.unavailable)
            core.invoke_command(cmd, {'kind': 'error',
                                      'message': msg % measure.name})
            if skip:
                self._skip_measure('SKIPPED',
                                   'Some runtime dependencies were unavailable'
                                   )
            return False

        store_key = 'build_deps' if kind == 'build' else 'runtime_deps'
        measure.store[store_key] = deps.dependencies

        return True

    # --- Private API ---------------------------------------------------------

    #: Collector of engines.
    _engines = Typed(ExtensionsCollector)

    #: Collector of editors.
    _editors = Typed(ExtensionsCollector)

    #: Collector of pre-execution hooks.
    _pre_hooks = Typed(ExtensionsCollector)

    #: Collectorsof monitors.
    _monitors = Typed(ExtensionsCollector)

    #: Collector of post-execution hooks.
    _post_hooks = Typed(ExtensionsCollector)

    def _listen_to_engine(self, status, infos):
        """Observer for the engine notifications.

        """
        meas = self.running_measure

        if not self.flags and MeasureFlags.no_post_exec:
            # Post execution should provide a way to interrupt their execution.
            meas.run_post_execution(self.workbench)

        mess = 'Measure {} processed, status : {}'.format(meas.name, status)
        logger.info(mess)

        # Releasing runtime dependencies.
        core = self.workbench.get_plugin('enaml.workbench.core')

        cmd = 'ecpy.app.dependencies.release_runtimes'
        core.invoke_command(cmd, {'dependencies': meas.store['runtime_deps'],
                                  'owner': self.manifest.id})

        # Disconnect monitors.
        engine = self.engine_instance
        if engine:
            engine.unobserve('news')

        # If we are supposed to stop, stop.
        if engine and self.flags & MeasureFlags.stop_processing:
            if self.engine_policy == 'stop':
                self._stop_engine()
            self.flags = 0

        # Otherwise find the next measure, if there is none stop the engine.
        else:
            meas = self.find_next_measure()
            if meas is not None:
                self.flags = 0
                self.start_measure(meas)
            else:
                if engine and self.engine_policy == 'stop':
                        self._stop_engine()
                self.flags = 0

    def _skip_measure(self, reason, message):
        """Skip a measure and provide an explanation for it.

        """
        # Simulate a message coming from the engine.
        done = {'value': (reason, message)}

        # Break a potential high statck as this function would not exit
        # if a new measure is started.
        enaml.application.deferred_call(self._listen_to_engine, done)

    def _stop_engine(self):
        """Stop the engine.

        """
        engine = self.engine_instance
        self.stop_processing()
        i = 0
        while engine and engine.active:
            sleep(0.5)
            i += 1
            if i > 10:
                self.force_stop_processing()

    def _post_setattr_selected_engine(self, old, new):
        """Ensures that the selected engine is informed when it is selected and
        deselected.

        This is always called before notifying the workspace of the change.

        """
        # Destroy old instance if any.
        self.engine_instance = None

        if old in self.engines:
            engine = self._engines.contributions[old]
            engine.react_to_unselection(self.workbench)

        if new and new in self.engines:
            engine = self._engines.contributions[new]
            engine.react_to_selection(self.workbench)

    def _update_contribs(self, name, change):
        """Update the list of available contribs when the contrib change.

        """
        setattr(self, name, list(getattr(self, '_'+name).contributions))
