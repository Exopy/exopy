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
from atom.api import Typed, Value, Property, set_default
from enaml.application import deferred_call
from enaml.workbench.ui.api import Workspace
from enaml.widgets.api import FileDialogEx
from enaml.layout.api import InsertItem, InsertTab

from ...utils.traceback import format_exc
from ...tasks.api import RootTask
from ..measure import Measure
from ..plugin import MeasurePlugin
from .measure_tracking import MeasureTracker

with enaml.imports():
    from .checks_display import ChecksDisplay
    from ..engines.selection import EngineSelector
    from .content import MeasureContent
    from .measure_edition import MeasureEditorDockItem
    from .tools_edition import ToolsEditorDockItem
    from .manifest import MeasureSpaceMenu


# ID used when adding handler to the logger.
LOG_ID = 'ecpy.measure.workspace'

logger = logging.getLogger(__name__)


LAYOUT = None


class MeasureSpace(Workspace):
    """Workspace dedicated tot measure edition and execution.

    """
    #: Reference to the plugin to which the workspace is linked.
    plugin = Typed(MeasurePlugin)

    #: Reference to the log panel model received from the log plugin.
    log_model = Value()

    #: Reference to the last edited measure used for saving.
    last_selected_measure = Property()

    window_title = set_default('Measure')

    def start(self):
        """Start the workspace, create a blanck measure if necessary and
        get engine contribution.

        """
        # Add a reference to the workspace in the plugin and keep a reference
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
        if not plugin.edited_measures.measures:
            self.new_measure()
        else:
            panels = self.plugin._workspace_state['measure_panels']
            self._insert_new_edition_panels(plugin.edited_measures.measures,
                                            False, panels)

        # Check whether or not an engine can contribute.
        if plugin.selected_engine:
            id_ = plugin.selected_engine
            engine = plugin.get_declarations('engine', [id_])[id_]
            deferred_call(engine.contribute_to_workspace, self)

        if self.plugin._workspace_state:
            self.dock_area.layout = self.plugin._workspace_state['layout']

        plugin.observe('selected_engine', self._update_engine_contribution)

        self._selection_tracker.start(plugin.edited_measures.measures[0])

    def stop(self):
        """Stop the workspace and clean.

        """
        plugin = self.plugin

        # Hide the monitors window. Not closing allow to preserve the
        # position and layout.
        if plugin.processor.monitors_window:
            plugin.processor.monitors_window.hide()

        plugin.unobserve('selected_engine', self._update_engine_contribution)

        if plugin.selected_engine:
            engine = plugin._engines.contributions[plugin.selected_engine]
            engine.clean_workspace(self)

        # HINT : we save the layout after removing the engine contribution.
        # which means that the layout is not prefectly preserved. To avoid that
        # we would need to insert the engine in sync way (not using
        # deferred_call) but this can lead to other issues.
        layout = self.dock_area.save_layout()

        m_edit_panels = [di for di in self.dock_area.dock_items() if
                         isinstance(di, MeasureEditorDockItem)]
        m_tools_panels = {di.measure: di for di in self.dock_area.dock_items()
                          if isinstance(di, ToolsEditorDockItem)}

        names = {di.measure: (di.name, getattr(m_tools_panels.get(di.measure),
                                               'name', ''))
                 for di in m_edit_panels}

        self.plugin._workspace_state = {'layout': layout,
                                        'measure_panels': names}

        # Remove handler from the root logger.
        core = self.workbench.get_plugin('enaml.workbench.core')
        cmd = 'ecpy.app.logging.remove_handler'
        core.invoke_command(cmd, {'id': LOG_ID}, self)

        self.workbench.unregister('ecpy.measure.workspace.menus')

        self.plugin.workspace = None

        self._selection_tracker.stop()

    def new_measure(self, dock_item=None):
        """Create a new edited measure using the default tools.

        Parameters
        ----------
        dock_item :
            Dock item used for editing the measure, if None a new item will be
            created and inserted in the dock area.

        """
        # TODO make sure this name is unique.
        measure = Measure(plugin=self.plugin, name='M', id='001')
        measure.root_task = RootTask()

        self._attach_default_tools(measure)

        self.plugin.edited_measures.add(measure)

        if dock_item is None:
            self._insert_new_edition_panels((measure,))

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
            path = os.path.join((measure.path or self.plugin.path),
                                measure.name + '.meas.ini')
            full_path = get_file(parent=self.content,
                                 current_path=path,
                                 name_filters=[u'*.meas.ini'])
            if not full_path:
                return
            elif not full_path.endswith('.meas.ini'):
                full_path += '.meas.ini'

            self.plugin.path = os.path.dirname(full_path)

        else:
            full_path = measure.path

        try:
            measure.save(full_path)
        except Exception:
            core = self.plugin.workbench.get_plugin('enaml.workbench.core')
            cmd = 'ecpy.app.errors.signal'
            msg = 'Failed to save measure :\n' + format_exc()
            core.invoke_command(cmd, dict(kind='error', message=msg))

    def load_measure(self, mode, dock_item=None):
        """ Load a measure.

        Parameters
        ----------
        mode : {'file', 'template'}
            In file mode, ask the user to specify a file from which to load a
            measure. In template mode, ask the user to choose a template and
            use the defaults settings of the plugin for the tools..

        """
        if mode == 'file':
            get_file = FileDialogEx.get_open_file_name
            full_path = get_file(name_filters=[u'*.meas.ini'],
                                 current_path=self.plugin.path)
            if not full_path:
                return

            measure, errors = Measure.load(self.plugin, full_path)
            if errors:
                core = self.plugin.workbench.get_plugin('enaml.workbench.core')
                cmd = 'ecpy.app.errors.signal'
                msg = 'Failed to load measure.'
                core.invoke_command(cmd, dict(kind='measure-loading',
                                              message=msg,
                                              details=errors))
                return

            self.plugin.edited_measures.add(measure)
            self.plugin.path = os.path.dirname(full_path)

        elif mode == 'template':
            # TODO create brand new measure using defaults from plugin and
            # load template
            raise NotImplementedError()

        if dock_item is None:
            self._insert_new_edition_panels((measure,))
        else:
            # If we were passed a dock item it means we are replacing an
            # existing measure with a different one, so the previous one is
            # not edited anymore.
            self.plugin.edited_measures.remove((dock_item.measure,))
            dock_item.measure = measure

        self._selection_tracker.set_selected_measure(measure)

        # HINT: code used to track ref leak to root task
        # requires to activtae root task instance tracking in tasks.base_tasks
#        def print_infos(root):
#            import gc
#            gc.collect()
#            import inspect
#            from ecpy.tasks.tasks.base_tasks import ROOTS
#            for r in ROOTS:
#                if r is not root:
#                    refs = [ref for ref in gc.get_referrers(r)
#                            if not inspect.isframe(ref)]
#                    print(('Root', refs))
#                    for ref in refs:
#                        print((ref,
#                               [re for re in gc.get_referrers(ref)
#                                if re is not refs and
#                                   not inspect.isframe(re)]))
#
#        deferred_call(print_infos, measure.root_task)

    # TODO : making this asynchronous or notifying the user would be super nice
    def enqueue_measure(self, measure):
        """Put a measure in the queue if it pass the tests.

        Parameters
        ----------
        measure : Measure
            Instance of Measure representing the measure.

        Returns
        -------
        bool
            True if the measure was successfully enqueued, False otherwise.

        """
        # Reset the forced enqueued flag
        measure.forced_enqueued = False

        # Collect the runtime dependencies
        res, msg, errors = measure.dependencies.collect_runtimes()

        if not res:
            if 'Failed' in msg:
                dial = ChecksDisplay(errors=errors, title=msg)
                dial.exec_()
                measure.dependencies.reset()
                return False

            # If some runtime are missing let the user know about it.
            else:
                msg = ('The following runtime dependencies of the measure {}, '
                       'are  not currently available. Some tests may be '
                       'skipped as a result but will be run before executing '
                       'the measure.\n Missing dependencies from :\n{}')
                msg = msg.format(measure.name,
                                 '\n'.join(('- '+id for id in errors)))
                # TODO : log as debug and display in popup
                logger.info(msg)

        # Run the checks specifying what runtimes are missing.
        check, errors = measure.run_checks(missing=errors.get('unavailable',
                                                              {}))

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
                    return False
        else:
            measure.dependencies.reset()
            dial = ChecksDisplay(errors=errors, is_warning=False)
            dial.exec_()
            if not dial.result:
                measure.dependencies.reset()
                return False
            measure.forced_enqueued = True

        default_filename = (measure.name + '_' + measure.id +
                            '.meas.ini')
        path = os.path.join(measure.root_task.default_path,
                            default_filename)

        old_path = measure.path
        measure.save(path)
        measure.path = old_path
        b_deps = measure.dependencies.get_build_dependencies()

        meas, errors = Measure.load(self.plugin, path, b_deps.dependencies)

        # Clean dependencies cache as at next enqueueing dependencies may have
        # changed
        measure.dependencies.reset()

        # Provide a nice error message.
        if not meas:
            measure.forced_enqueued = False
            msg = 'Failed to rebuild measure from config'
            dial = ChecksDisplay(errors={'Building': errors}, title=msg)
            dial.exec_()
            return False

        meas.forced_enqueued = measure.forced_enqueued

        try:
            os.remove(path)
        except OSError:
            logger.debug('Failed to remove temp save file')

        meas.status = 'READY'
        meas.infos = 'The measure is ready to be performed by an engine.'
        self.plugin.enqueued_measures.add(meas)

        return True

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
            if measure.status in ('SKIPPED', 'FAILED', 'COMPLETED',
                                  'INTERRUPTED'):
                self.plugin.enqueued_measures.remove(measure)

    def start_processing_measures(self):
        """ Starts to perform the measurement in the queue.

        Measure will be processed in their order of appearance in the queue.

        """
        if not self._ensure_selected_engine():
            return

        measure = self.plugin.find_next_measure()
        self.plugin.processor.continuous_processing = True
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
        if not self._ensure_selected_engine():
            return

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
        self.plugin.processor.stop_measure(no_post_exec, force)

    def stop_processing_measures(self, no_post_exec=False, force=False):
        """Stop processing enqueued measure.

        """
        self.plugin.processor.stop_processing(no_post_exec, force)

    @property
    def dock_area(self):
        """ Getter for the dock_area of the content.

        """
        if self.content and self.content.children:
            return self.content.children[1]

    # --- Private API ---------------------------------------------------------

    #: Background thread determining the last edited measure by analysing the
    #: last selected widget.
    _selection_tracker = Typed(MeasureTracker, ())

    def _attach_default_tools(self, measure):
        """Add the default tools to a measure.

        """
        # TODO : use error plugin to report that kind of issues
        for pre_id in self.plugin.default_pre_hooks:
            if pre_id in self.plugin.pre_hooks:
                measure.add_tool('pre-hook', pre_id)
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
                measure.add_tool('post-hook', post_id)
            else:
                msg = "Default post-execution hook {} not found"
                logger.warn(msg.format(post_id))

    def _insert_new_edition_panels(self, measures, update=True, panels=None):
        """Handle inserting a new MeasureEditorDockItem in the content.

        """
        if panels is None:
            template = 'meas_%d'
            items = self.dock_area.dock_items()
            test = re.compile('meas\_([0-9]+)$')
            measure_items = [i for i in items if test.match(i.name)]

            ops = []
            for measure in measures:
                if not measure_items:
                    name = template % 0
                    ops.append(InsertItem(item=name, target='meas_exec'))
                else:
                    indexes = [int(test.match(i.name).group(1))
                               for i in measure_items]
                    indexes.sort()

                    if len(indexes) <= max(indexes):
                        ind = [i for i, x in enumerate(indexes) if i != x][0]
                    else:
                        ind = len(measure_items)

                    name = template % ind
                    ops.append(InsertTab(item=name,
                                         target=template % indexes[0]))

                measure_items.append(MeasureEditorDockItem(self.dock_area,
                                                           workspace=self,
                                                           measure=measure,
                                                           name=name))

            if update:
                deferred_call(self.dock_area.update_layout, ops)
        else:
            for m in measures:
                if m not in panels:
                    msg = ('Cannot insert edition panels for measure %s, no '
                           'infos were provided. Panels exists for:\n%s')
                    raise RuntimeError(msg % (m.name + ' (id : %s)' % m.id,
                                              ', '.join(m.name for m in panels)
                                              )
                                       )
                ed_name, t_name = panels[m]
                MeasureEditorDockItem(self.dock_area, workspace=self,
                                      measure=m, name=ed_name)
                if t_name:
                    ToolsEditorDockItem(self.dock_area, measure=m,
                                        name=t_name)

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
            engine.contribute_to_workspace(self)

    def _get_last_selected_measure(self):
        """Wait for the background to finish processing the selected widgets.

        """
        return self._selection_tracker.get_selected_measure()

    def _ensure_selected_engine(self):
        """Make sure an engine is selected and if not prompt the user to choose
        one.

        """
        if not self.plugin.selected_engine:
            dial = EngineSelector(plugin=self.plugin)
            if dial.exec_() and dial.selected_decl:
                self.plugin.selected_engine = dial.selected_decl.id

        return bool(self.plugin.selected_engine)
