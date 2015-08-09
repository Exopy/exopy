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
from inspect import cleandoc
from functools import partial
from enum import IntEnum

import enaml
from atom.api import Typed, Unicode, List, ForwardTyped, Int

from ..utils.plugin_tools import HasPrefPlugin, ExtensionsCollector
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


# XXXX
def check_engine(engine):
    """
    """
    pass


# XXXX
def check_editor(editor):
    """
    """
    pass


# XXXX
def check_pre_hook(pre_hook):
    """
    """
    pass


# XXXX
def check_monitor(monitor):
    """
    """
    pass


# XXXX
def check_post_hook(post_hook):
    """
    """
    pass


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

    #: Currently edited measures.
    edited_measures = List()

    #: Currently enqueued measures.
    enqueued_measures = List()

    #: Currently run measure or last measure run.
    running_measure = Typed(Measure)

    #: List of currently available engines.
    engines = List()

    #: Currently selected engine represented by its id.
    selected_engine = Unicode().tag(pref=True)

    #: Instance of the currently used engine.
    engine_instance = Typed(BaseEngine)

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

        self._engines = ExtensionsCollector(workbench=self.workbench,
                                            point=ENGINES_POINT,
                                            ext_class=Engine,
                                            validate_ext=check_engine)
        self._engines.start()
        self._editors = ExtensionsCollector(workbench=self.workbench,
                                            point=EDITORS_POINT,
                                            ext_class=Editor,
                                            validate_ext=check_editor)
        self._editors.start()
        self._pre_hooks = ExtensionsCollector(workbench=self.workbench,
                                              point=PRE_HOOK_POINT,
                                              ext_class=PreExecutionHook,
                                              validate_ext=check_pre_hook)
        self._pre_hooks.start()
        self._monitors = ExtensionsCollector(workbench=self.workbench,
                                             point=MONITORS_POINT,
                                             ext_class=Monitor,
                                             validate_ext=check_monitor)
        self._monitors.start()
        self._post_hooks = ExtensionsCollector(workbench=self.workbench,
                                               point=POST_HOOK_POINT,
                                               ext_class=PostExecutionHook,
                                               validate_ext=check_post_hook)
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

    def create(self, kind, id, bare=False):
        """Create a new instance of an engine/editor/tool.

        Parameters
        ----------
        kind : {'engine', 'editor', 'pre-hook', 'monitor', 'post-hook'}
            Kind of object to create.

        id : unicode
            Id of the object to create.

        bare : bool, optional
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

        return decls[id].new(self.workbench)

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

        # XXXX refactor as this is not generic enough. We might have other
        # runtmes with permissions.
        instr_use_granted = 'profiles' not in measure.store
        # Checking build dependencies, if present simply request instr profiles
        if 'build_deps' in measure.store and 'profiles' in measure.store:
            # Requesting profiles as this is the only missing runtime.
            core = self.workbench.get_plugin('enaml.workbench.core')
            profs = measure.store['profiles']
            if not profs:
                cmd = u'hqc_meas.dependencies.collect_dependencies'
                id = 'hqc_meas.instruments.dependencies'
                res = core.invoke_command(cmd,
                                          {'obj': measure.root_task,
                                           'ids': [id],
                                           'dependencies': ['runtime']},
                                          self)

                profiles = res[1].get('profiles', [])
                measure.store['profiles'] = profiles.keys()

            else:
                com = u'hqc_meas.instr_manager.profiles_request'
                profiles, _ = core.invoke_command(com,
                                                  {'profiles': list(profs)},
                                                  self)

            instr_use_granted = not bool(profs) or profiles
            measure.root_task.run_time.update({'profiles': profiles})

        else:
            # Rebuild build and runtime dependencies (profiles automatically)
            # re-requested.
            core = self.workbench.get_plugin('enaml.workbench.core')
            cmd = u'hqc_meas.dependencies.collect_dependencies'
            res = core.invoke_command(cmd, {'obj': measure.root_task}, self)
            if not res[0]:
                for id in res[1]:
                    logger.warn(res[1][id])
                return False

            build_deps = res[1]
            runtime_deps = res[2]

            instr_use_granted = 'profiles' not in runtime_deps or\
                runtime_deps['profiles']

            measure.store['build_deps'] = build_deps
            if 'profiles' in runtime_deps:
                measure.store['profiles'] = runtime_deps['profiles']
            measure.root_task.run_time = runtime_deps

        if not instr_use_granted:
            mes = cleandoc('''The instrument profiles requested for the
                           measurement {} are not available, the measurement
                           cannot be performed.'''.format(measure.name))
            logger.info(mes.replace('\n', ' '))

            # Simulate a message coming from the engine.
            done = {'value': ('SKIPPED', 'Failed to get requested profiles')}

            # Break a potential high statck as this function would not exit
            # if a new measure is started.
            enaml.application.deferred_call(self._listen_to_engine, done)
            return

        else:
            if 'profiles' in measure.store:
                mess = cleandoc('''The use of the instrument profiles has been
                                granted by the manager.''')
                logger.info(mess.replace('\n', ' '))

        # XXXX Must run all pre-execution hooks
        # Run internal test to check communication.
        res, errors = measure.run_checks(self.workbench, True, True)
        if not res:
            mes = cleandoc('''The measure failed to pass the built-in tests,
                           this is likely related to a connection error to an
                           instrument.
                           '''.format(measure.name))
            logger.warn(mes.replace('\n', ' '))

            # Simulate a message coming from the engine.
            done = {'value': ('FAILED', 'Failed to pass the built in tests')}

            # Break a potential high statck as this function would not exit
            # if a new measure is started.
            enaml.application.deferred_call(self._listen_to_engine, done)
            return

        # Start the engine if it has not already been done.
        if not self.engine_instance:
            decl = self.engines[self.selected_engine]
            engine = decl.factory(decl, self.workbench)
            self.engine_instance = engine

            # Connect signal handler to engine.
            engine.observe('completed', self._listen_to_engine)

            # Connect engine measure status to observer
            engine.observe('measure_status', self._update_measure_status)

        engine = self.engine_instance

        # Call engine prepare to run method.
        entries = measure.collect_entries_to_observe()
        engine.prepare_to_run(measure.name, measure.root_task, entries,
                              measure.store['build_deps'])

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

    def stop_measure(self):
        """Stop the currently active measure.

        """
        logger.info('Stopping measure {}.'.format(self.running_measure.name))
        self.flags |= MeasureFlags.stop_attempt
        self.engine_instance.stop()

    def stop_processing(self):
        """Stop processing the enqueued measure.

        """
        logger.info('Stopping measure {}.'.format(self.running_measure.name))
        self.flags |= MeasureFlags.stop_attempt | MeasureFlags.stop_processing
        if self.flags and MeasureFlags.processing:
            self.flags &= ~MeasureFlags.processing
        self.engine_instance.exit()

    def force_stop_measure(self):
        """Force the engine to stop performing the current measure.

        """
        logger.info('Exiting measure {}.'.format(self.running_measure.name))
        self.engine_instance.force_stop()

    def force_stop_processing(self):
        """Force the engine to exit and stop processing measures.

        """
        logger.info('Exiting measure {}.'.format(self.running_measure.name))
        self.flags |= MeasureFlags.stop_processing
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

    # XXXX
    def _listen_to_engine(self, status, infos):
        """ Observer for the engine notifications.

        """
        mess = 'Measure {} processed, status : {}'.format(
            self.running_measure.name, status)
        logger.info(mess)

        # XXXX Generalize to any kind of runtime.
        # Releasing instrument profiles.
        profs = self.running_measure.store.get('profiles', set())
        core = self.workbench.get_plugin('enaml.workbench.core')

        com = u'hqc_meas.instr_manager.profiles_released'
        core.invoke_command(com, {'profiles': list(profs)}, self)

        # Disconnect monitors.
        engine = self.engine_instance
        if engine:
            engine.unobserve('news')


        # XXXX refactor to avoid code duplication and add way to keep engine
        # in sleep mode (sometimes very costly to start an engine).
        # If we are supposed to stop, stop.
        if engine and self.flags & MeasureFlags.stop_processing:
            self.stop_processing()
            i = 0
            while engine and engine.active:
                sleep(0.5)
                i += 1
                if i > 10:
                    self.force_stop_processing()
            self.flags = 0

        # Otherwise find the next measure, if there is none stop the engine.
        else:
            meas = self.find_next_measure()
            if meas is not None:
                self.flags = 0
                self.start_measure(meas)
            else:
                if engine:
                    self.stop_processing()
                    i = 0
                    while engine.active:
                        sleep(0.5)
                        i += 1
                        if i > 10:
                            self.force_stop_processing()
                self.flags = 0

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
