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

import enaml
from atom.api import Typed, Unicode, List, ForwardTyped

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


def _workspace():
    from .workspace import MeasureSpace
    return MeasureSpace


def check_engine(engine):
    """
    """
    pass


def check_editor(editor):
    """
    """
    pass


def check_pre_hook(pre_hook):
    """
    """
    pass


def check_monitor(monitor):
    """
    """
    pass


def check_post_hook(post_hook):
    """
    """
    pass


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

    # XXXX
    engines = List()

    #: Currently selected engine represented by its id.
    selected_engine = Unicode().tag(pref=True)

    #: Instance of the currently used engine.
    engine_instance = Typed(BaseEngine)

    # XXXX
    pre_hooks = List()

    # Default pre-execution hooks to use for new measures.
    default_pre_hooks = List().tag(pref=True)

    # XXXX
    monitors = List()

    # Default monitors to use for new measures.
    default_monitors = List().tag(pref=True)

    # XXXX
    post_hooks = List()

    # Default post-execution hooks to use for new measures.
    default_hooks = List().tag(pref=True)

    # Dict holding the contributed Editor declarations
    editors = List()

    # XXXX
    # Internal flags.
    flags = List()

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

    # XXXX
    def start_measure(self, measure):
        """ Start a new measure.

        """
        logger = logging.getLogger(__name__)

        # Discard old monitors if there is any remaining.
        if self.running_measure:
            for monitor in self.running_measure.monitors.values():
                monitor.stop()

        measure.enter_running_state()
        self.running_measure = measure

        self.flags.append('processing')

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

        # Collect headers.
        measure.collect_headers(self.workbench)

        # Start the engine if it has not already been done.
        if not self.engine_instance:
            decl = self.engines[self.selected_engine]
            engine = decl.factory(decl, self.workbench)
            self.engine_instance = engine

            # Connect signal handler to engine.
            engine.observe('done', self._listen_to_engine)

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

    # XXXX
    def pause_measure(self):
        """ Pause the currently active measure.

        """
        logger = logging.getLogger(__name__)
        logger.info('Pausing measure {}.'.format(self.running_measure.name))
        self.engine_instance.pause()

    # XXXX
    def resume_measure(self):
        """ Resume the currently paused measure.

        """
        logger = logging.getLogger(__name__)
        logger.info('Resuming measure {}.'.format(self.running_measure.name))
        self.engine_instance.resume()

    # XXXX
    def stop_measure(self):
        """ Stop the currently active measure.

        """
        logger = logging.getLogger(__name__)
        logger.info('Stopping measure {}.'.format(self.running_measure.name))
        self.flags.append('stop_attempt')
        self.engine_instance.stop()

    # XXXX
    def stop_processing(self):
        """ Stop processing the enqueued measure.

        """
        logger = logging.getLogger(__name__)
        logger.info('Stopping measure {}.'.format(self.running_measure.name))
        self.flags.append('stop_attempt')
        self.flags.append('stop_processing')
        if 'processing' in self.flags:
            self.flags.remove('processing')
        self.engine_instance.exit()

    # XXXX
    def force_stop_measure(self):
        """ Force the engine to stop performing the current measure.

        """
        logger = logging.getLogger(__name__)
        logger.info('Exiting measure {}.'.format(self.running_measure.name))
        self.engine_instance.force_stop()

    # XXXX
    def force_stop_processing(self):
        """ Force the engine to exit and stop processing measures.

        """
        logger = logging.getLogger(__name__)
        logger.info('Exiting measure {}.'.format(self.running_measure.name))
        self.flags.append('stop_processing')
        if 'processing' in self.flags:
            self.flags.remove('processing')
        self.engine_instance.force_exit()

    # XXXX
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

    # XXXX
    _engines = Typed(ExtensionsCollector)

    # XXXX
    _editors = Typed(ExtensionsCollector)

    # XXXX
    _pre_hooks = Typed(ExtensionsCollector)

    # XXXX
    _monitors = Typed(ExtensionsCollector)

    # XXXX
    _post_hooks = Typed(ExtensionsCollector)

    # XXXX
    def _listen_to_engine(self, change):
        """ Observer for the engine notifications.

        """
        status, infos = change['value']
        self.running_measure.status = status
        self.running_measure.infos = infos

        logger = logging.getLogger(__name__)
        mess = 'Measure {} processed, status : {}'.format(
            self.running_measure.name, status)
        logger.info(mess)

        # Releasing instrument profiles.
        profs = self.running_measure.store.get('profiles', set())
        core = self.workbench.get_plugin('enaml.workbench.core')

        com = u'hqc_meas.instr_manager.profiles_released'
        core.invoke_command(com, {'profiles': list(profs)}, self)

        # Disconnect monitors.
        engine = self.engine_instance
        if engine:
            engine.unobserve('news')

        # If we are supposed to stop, stop.
        if engine and'stop_processing' in self.flags:
            self.stop_processing()
            i = 0
            while engine and engine.active:
                sleep(0.5)
                i += 1
                if i > 10:
                    self.force_stop_processing()
            self.flags = []

        # Otherwise find the next measure, if there is none stop the engine.
        else:
            meas = self.find_next_measure()
            if meas is not None:
                self.flags = []
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
                self.flags = []

    def _post_setattr_selected_engine(self, old, new):
        """Observer ensuring that the selected engine is informed when it is
        selected and deselected.

        """
        # Destroy old instance if any.
        self.engine_instance = None

        if old in self.engines:
            engine = self.engines[old]
            engine.post_deselection(engine, self.workbench)

        if new and new in self.engines:
            engine = self.engines[new]
            engine.post_selection(engine, self.workbench)

    def _update_contribs(self, name, change):
        """Update the list of available contribs when the contrib change.

        """
        setattr(self, name, list(getattr(self, '_'+name).contributions))
