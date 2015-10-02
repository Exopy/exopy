# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Workspace used for editing and executing measures.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import logging
import os
import re

import enaml
from atom.api import Typed, Value, set_default
from enaml.application import deferred_call
from enaml.workbench.ui.api import Workspace
from enaml.widgets.api import FileDialogEx
from enaml.layout.api import InsertItem

from .measure import Measure
from .plugin import MeasurePlugin
from ..tasks.api import RootTask

with enaml.imports():
    from .checks_display import ChecksDisplay
    from .engines.selection import EngineSelector
    from .content import MeasureContent
    from .measure_edition import MeasureEditorDockItem
    from .manifest import MeasureSpaceMenu


# ID used when adding handler to the logger.
LOG_ID = 'ecpy.measure.workspace'

logger = logging.getLogger(__name__)


class MeasureSpace(Workspace):
    """Workspace dedicated tot measure edition and execution.

    """
    #: Reference to the plugin to which the workspace is linked.
    plugin = Typed(MeasurePlugin)

    #: Reference to the log panel model received from the log plugin.
    log_model = Value()

    #: Reference to the last currently edited measure the user selected.
    last_selected_measure = Typed(Measure)

    window_title = set_default('Measure')

    def start(self):
        """Start the workspace, create a blanck measure if necessary and
        get engine contribution.

        """
        # Add a reference to thet workspace in the plugin and keep a reference
        # to the plugin.
        plugin = self.workbench.get_plugin('ecpy.measure')
        plugin.workspace = self
        self.plugin = plugin

        # Add handler to the root logger to display messages in panel.
        core = self.workbench.get_plugin('enaml.workbench.core')
        cmd = 'ecpy.app.logging.add_handler'
        self.log_model = core.invoke_command(cmd,
                                             {'id': LOG_ID, 'mode': 'ui'},
                                             self)[0]

        # Create content.
        self.content = MeasureContent(workspace=self)

        # Contribute menus.
        self.workbench.register(MeasureSpaceMenu(workspace=self))

        # Check whether or not a measure is already being edited.
        if not plugin.edited_measures:
            self.new_measure()
        else:
            for measure in self.plugin.enqueued_measures:
                self._insert_new_edition_panel(measure)

        # Check whether or not an engine can contribute.
        if plugin.selected_engine:
            id = plugin.selected_engine
            engine = plugin.get_declarations('engine', [id])[id]
            deferred_call(engine.contribute_workspace, self)

        plugin.observe('selected_engine', self._update_engine_contribution)

        # TODO implement layout reloading so that we can easily switch between
        # workspaces.

    def stop(self):
        """Stop the workspace and clean.

        """
        plugin = self.plugin

        # Hide the monitors window. Not closing allow to preserve the
        # position and layout.
        plugin.processor.monitors_window.hide()

        plugin.unobserve('selected_engine', self._update_engine_contribution)

        if plugin.selected_engine:
            engine = plugin._engines.contributions[plugin.selected_engine]
            engine.clean_workspace(self)

        # Remove handler from the root logger.
        core = self.workbench.get_plugin('enaml.workbench.core')
        cmd = 'ecpy.app.logging.remove_handler'
        core.invoke_command(cmd, {'id': LOG_ID}, self)

        self.workbench.unregister('ecpy.measure.workspace.menus')

        self.plugin.workspace = None

        # TODO implement layout saving so that we can easily switch between
        # workspaces.

    def new_measure(self, dock_item=None):
        """ Create a new measure using the default tools.

        Parameters
        ----------
        dock_item :
            Dock item used for editing the measure, if None a new item will be
            created and inserted in the dock area.

        """
        measure = Measure(plugin=self.plugin)
        measure.root_task = RootTask()

        self._attach_default_tools(measure)

        self.plugin.edited_measures.add(measure)

        if dock_item is None:
            self._insert_new_edition_panel(measure)

    def save_measure(self, measure, auto=True):
        """ Save a measure in a file.

        Parameters
        ----------
        measure : Measure
            Measure to save.

        auto : bool, optional
            When true if a path is associated to the measure save it there,
            otherwise ask the user where to save it.

        """
        if not auto or not measure.path:
            get_file = FileDialogEx.get_save_file_name
            path = measure.path or self.plugin.path
            full_path = get_file(parent=self.content,
                                 current_path=path,
                                 name_filters=[u'*.meas.ini'])
            if not full_path:
                return
            elif not full_path.endswith('.meas.ini'):
                full_path += '.meas.ini'

            self.plugin.path = full_path

        else:
            full_path = measure.path

        # XXXX add try except
        measure.save(full_path)

    def load_measure(self, mode, dock_item=None):
        """ Load a measure.

        Parameters
        ----------
        mode : str
            file: ask the user to specify a file from which to load a measure.
            template: ask the user to choose a template and use default for the
                rest.

        """
        if mode == 'file':
            get_file = FileDialogEx.get_open_file_name
            full_path = get_file(name_filters=[u'*.meas.ini'],
                                 current_path=self.plugin.path)
            if not full_path:
                return

            measure, errors = Measure.load(self.plugin, full_path)
            # XXXX handle errors
            self.plugin.edited_measure.add(measure)
            self.plugin.path = full_path

        elif mode == 'template':
            # TODO create brand new measure using defaults from plugin and
            # load template
            raise NotImplementedError()

        if dock_item is None:
            self._insert_new_edition_panel(measure)

    # TODO : making this asynchronous or notifying the user would be super nice
    def enqueue_measure(self, measure):
        """Put a measure in the queue if it pass the tests.

        Parameters
        ----------
        measure : Measure
            Instance of Measure representing the measure.

        Returns
        -------
        bool :
            True is the measure was successfully enqueued, False otherwise.

        """
        # Collect the runtime dependencies
        res, msg, errors = measure.collect_runtimes()

        if not res:
            if 'Failed' in msg:
                dial = ChecksDisplay(errors=errors, title=msg)
                dial.exec_()
                return

            # If some runtime are missing let the user know about it.
            else:
                msg = ('The following runtime dependencies of the measure {}, '
                       'are  not currently available. Some tests may be '
                       'skipped as a  result but will be run before executing '
                       'the measure.\n Missing dependencies from :\n{}')
                msg.format(measure.name,
                           '\n'.join(('-'+id for id in errors['unavailable'])))
                logger.info(msg)

        # Run the checks specifying what runtimes are missing.
        check, errors = measure.run_checks(self.workbench,
                                           missing=errors['unavailable'])

        # Release the runtimes.
        measure.dependencies.release_runtimes()

        if check:
            # If check is ok but there are some errors, those are warnings
            # which the user can either ignore and enqueue the measure, or he
            # can cancel the enqueuing and try again.
            if errors:
                dial = ChecksDisplay(errors=errors, is_warning=True)
                dial.exec_()
                if not dial.result:
                    measure.dependencies.reset()
                    return

            default_filename = (measure.name + '_' + measure.id +
                                '.meas.ini')
            path = os.path.join(measure.root_task.default_path,
                                default_filename)
            measure.save(path)
            b_deps = measure.dependencies.get_build_dependencies()

            meas, errors = Measure.load(self.plugin, path, b_deps)
            # Provide a nice error message.
            if not meas:
                msg = 'Failed to rebuild measure from config'
                dial = ChecksDisplay(errors={'internal': errors}, title=msg)
                dial.exec_()
                return
            try:
                os.remove(path)
            except OSError:
                logger.debug('Failed to remove temp save file')

            meas.status = 'READY'
            meas.infos = 'The measure is ready to be performed by an engine.'
            self.plugin.enqueued_measures.add(meas)

            return True

        else:
            measure.dependencies.reset()
            ChecksDisplay(errors=errors).exec_()
            return False

    def reenqueue_measure(self, measure):
        """ Mark a measure already in queue as fitted to be executed.

        This method can be used to re-enqueue a measure that previously failed,
        for example because a profile was missing, the measure can then be
        edited again and will be executed in its turn.

        WARNING : the test are run again !!!

        Parameters
        ----------
        measure : Measure
            The measure to re-enqueue

        """
        measure.enter_edition_state()
        measure.status = 'READY'
        measure.infos = 'Measure re-enqueued by the user'

    def remove_processed_measures(self):
        """ Remove all the measures which have been processed from the queue.

        This method rely on the status of the measure. Only measures whose
        status is 'READY' will be left in the queue.

        """
        for measure in self.plugin.enqueued_measures.measures[:]:
            if measure.status != 'READY':
                self.plugin.enqueued_measures.remove(measure)

    def start_processing_measures(self):
        """ Starts to perform the measurement in the queue.

        Measure will be processed in their order of appearance in the queue.

        """
        if not self.plugin.selected_engine:
            dial = EngineSelector(plugin=self.plugin)
            dial.exec_()
            if dial.selected_id:
                self.plugin.selected_engine = dial.selected_decl.id
            else:
                return

        measure = self.plugin.find_next_measure()
        self.plugin.processor.continuous_processing = False
        if measure is not None:
            self.plugin.processor.start_measure(measure)
        else:
            cmd = 'ecpy.app.errors.signal'
            core = self.workbench.get_plugin('enaml.workbench.core')
            msg = 'None of the curently enqueued measures can be run.'
            core.invoke_command(cmd, {'kind': 'error', 'message': msg})

    def process_single_measure(self, measure):
        """ Performs a single measurement and then stops.

        Parameters
        ----------
        measure : Measure
            Measure to perform.

        """
        self.plugin.processor.continuous_processing = False

        self.plugin.processor.start_measure(measure)

    def pause_current_measure(self):
        """Pause the currently active measure.

        """
        self.plugin.processor.pause_measure()

    def resume_current_measure(self):
        """Resume the currently paused measure.

        """
        self.plugin.processor.resume_measure()

    def stop_current_measure(self, no_post_exec=False, force=False):
        """Stop the execution of the currently executed measure.

        """
        self.plugin.processor.stop_measure(force, no_post_exec)

    def stop_processing_measures(self, no_post_exec=False, force=False):
        """Stop processing enqueued measure.

        """
        self.plugin.processor.stop_processing(force, no_post_exec)

    @property
    def dock_area(self):
        """ Getter for the dock_area of the content.

        """
        if self.content and self.content.children:
            return self.content.children[0]

    # --- Private API ---------------------------------------------------------

    def _attach_default_tools(self, measure):
        """Add the default tools to a measure.

        """
        for pre_id in self.plugin.default_pre_hooks:
            if pre_id in self.plugin.pre_hooks:
                measure.add_tool('pre_hook', pre_id)
            else:
                msg = "Default pre-execution hook {} not found"
                logger.warn(msg.format(pre_id))

        for monitor_id in self.plugin.default_monitors:
            if monitor_id in self.plugin.monitors:
                measure.add_tool('monitor', monitor_id)
            else:
                msg = "Default monitor {} not found."
                logger.warn(msg.format(monitor_id))

        for post_id in self.plugin.default_post_hooks:
            if post_id in self.plugin.post_hooks:
                measure.add_tool('post_hook', post_id)
            else:
                msg = "Default post-execution hook {} not found"
                logger.warn(msg.format(post_id))

    def _insert_new_edition_panel(self, measure, dock_name=None):
        """Handle inserting a new MeasureEditorDockItem in the content.

        """
        template = 'meas_%d'
        items = self.dock_area.dock_items()
        test = re.compile('meas\_([0-9]+)$')
        measure_items = filter(lambda i: test.match(i.name), items)

        if not measure_items:
            op = InsertItem(item=template % 0, target='meas_exec')
        else:
            indexes = [int(test.match(i.name).group(1))
                       for i in measure_items]
            indexes.sort()
            missings = [i for i, (i1, i2) in enumerate(zip(indexes[:-1],
                                                           indexes[1:]))
                        if i1 + 1 != i2]

            if missings:
                ind = missings[0]
            else:
                ind = len(measure_items)

            op = InsertItem(item=template % ind, target=measure_items[-1])

        MeasureEditorDockItem(self.dock_area, workspace=self,
                              measure=measure)
        self.dock_area.update_layout(op)

    def _update_engine_contribution(self, change):
        """Make sure that the engine contribution to the workspace does reflect
        the currently selected engine.

        """
        if 'oldvalue' in change:
            old = change['oldvalue']
            if old in self.plugin.engines:
                engine = self.plugin.get_declarations('engine', [old])[old]
                engine.clean_workspace(self)

        new = change['value']
        if new and new in self.plugin.engines:
            engine = self.plugin.get_declarations('engine', [new])[new]
            engine.clean_workspace(self)
