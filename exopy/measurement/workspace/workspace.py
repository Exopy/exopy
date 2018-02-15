# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Workspace used for editing and executing measurements.

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
from ..measurement import Measurement
from ..plugin import MeasurementPlugin
from .measurement_tracking import MeasurementTracker

with enaml.imports():
    from .checks_display import ChecksDisplay
    from ..engines.selection import EngineSelector
    from .content import MeasureContent
    from .measurement_edition import MeasurementEditorDockItem
    from .tools_edition import ToolsEditorDockItem
    from .manifest import MeasurementSpaceMenu


# ID used when adding handler to the logger.
LOG_ID = 'exopy.measurement.workspace'

logger = logging.getLogger(__name__)


LAYOUT = None


class MeasurementSpace(Workspace):
    """Workspace dedicated tot measurement edition and execution.

    """
    #: Reference to the plugin to which the workspace is linked.
    plugin = Typed(MeasurementPlugin)

    #: Reference to the log panel model received from the log plugin.
    log_model = Value()

    #: Reference to the last edited measurement used for saving.
    last_selected_measurement = Property()

    window_title = set_default('Measurement')

    def start(self):
        """Start the workspace, create a blanck measurement if necessary and
        get engine contribution.

        """
        # Add a reference to the workspace in the plugin and keep a reference
        # to the plugin.
        plugin = self.workbench.get_plugin('exopy.measurement')
        plugin.workspace = self
        self.plugin = plugin

        # Add handler to the root logger to display messages in panel.
        core = self.workbench.get_plugin('enaml.workbench.core')
        cmd = 'exopy.app.logging.add_handler'
        self.log_model = core.invoke_command(cmd,
                                             {'id': LOG_ID, 'mode': 'ui'},
                                             self)[0]

        # Create content.
        self.content = MeasureContent(workspace=self)

        # Contribute menus.
        self.workbench.register(MeasurementSpaceMenu(workspace=self))

        # Check whether or not a measurement is already being edited.
        if not plugin.edited_measurements.measurements:
            self.new_measurement()
        else:
            panels = self.plugin._workspace_state['measurement_panels']
            self._insert_new_edition_panels(
                plugin.edited_measurements.measurements,
                False, panels)

        # Check whether or not an engine can contribute.
        if plugin.selected_engine:
            id_ = plugin.selected_engine
            engine = plugin.get_declarations('engine', [id_])[id_]
            deferred_call(engine.contribute_to_workspace, self)

        if self.plugin._workspace_state:
            self.dock_area.layout = self.plugin._workspace_state['layout']

        plugin.observe('selected_engine', self._update_engine_contribution)

        self._selection_tracker.start(
            plugin.edited_measurements.measurements[0])

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
                         isinstance(di, MeasurementEditorDockItem)]
        m_tools_panels = {di.measurement: di
                          for di in self.dock_area.dock_items()
                          if isinstance(di, ToolsEditorDockItem)}

        names = {di.measurement: (di.name,
                                  getattr(m_tools_panels.get(di.measurement),
                                          'name', ''))
                 for di in m_edit_panels}

        self.plugin._workspace_state = {'layout': layout,
                                        'measurement_panels': names}

        # Remove handler from the root logger.
        core = self.workbench.get_plugin('enaml.workbench.core')
        cmd = 'exopy.app.logging.remove_handler'
        core.invoke_command(cmd, {'id': LOG_ID}, self)

        self.workbench.unregister('exopy.measurement.workspace.menus')

        self.plugin.workspace = None

        self._selection_tracker.stop()

    def new_measurement(self, dock_item=None):
        """Create a new edited measurement using the default tools.

        Parameters
        ----------
        dock_item :
            Dock item used for editing the measurement, if None a new item will
            be created and inserted in the dock area.

        """
        # TODO make sure this name is unique.
        measurement = Measurement(plugin=self.plugin, name='M', id='001')
        measurement.root_task = RootTask()

        self._attach_default_tools(measurement)

        self.plugin.edited_measurements.add(measurement)

        if dock_item is None:
            self._insert_new_edition_panels((measurement,))

    def save_measurement(self, measurement, auto=True):
        """ Save a measurement in a file.

        Parameters
        ----------
        measurement : Measurement
            Measurement to save.

        auto : bool, optional
            When true if a path is associated to the measurement save it there,
            otherwise ask the user where to save it.

        """
        if not auto or not measurement.path:
            get_file = FileDialogEx.get_save_file_name
            path = os.path.join((measurement.path or self.plugin.path),
                                measurement.name + '.meas.ini')
            full_path = get_file(parent=self.content,
                                 current_path=path,
                                 name_filters=[u'*.meas.ini'])
            if not full_path:
                return
            elif not full_path.endswith('.meas.ini'):
                full_path += '.meas.ini'

            self.plugin.path = os.path.dirname(full_path)

        else:
            full_path = measurement.path

        try:
            measurement.save(full_path)
        except Exception:
            core = self.plugin.workbench.get_plugin('enaml.workbench.core')
            cmd = 'exopy.app.errors.signal'
            msg = 'Failed to save measurement :\n' + format_exc()
            core.invoke_command(cmd, dict(kind='error', message=msg))

    def load_measurement(self, mode, dock_item=None):
        """ Load a measurement.

        Parameters
        ----------
        mode : {'file', 'template'}
            In file mode, ask the user to specify a file from which to load a
            measurement. In template mode, ask the user to choose a template
            and use the defaults settings of the plugin for the tools..

        """
        if mode == 'file':
            get_file = FileDialogEx.get_open_file_name
            full_path = get_file(name_filters=[u'*.meas.ini'],
                                 current_path=self.plugin.path)
            if not full_path:
                return

            measurement, errors = Measurement.load(self.plugin, full_path)
            if errors:
                core = self.plugin.workbench.get_plugin('enaml.workbench.core')
                cmd = 'exopy.app.errors.signal'
                msg = 'Failed to load measurement.'
                core.invoke_command(cmd, dict(kind='measurement-loading',
                                              message=msg,
                                              details=errors))
                return

            self.plugin.edited_measurements.add(measurement)
            self.plugin.path = os.path.dirname(full_path)

        elif mode == 'template':
            # TODO create brand new measurement using defaults from plugin and
            # load template
            raise NotImplementedError()

        if dock_item is None:
            self._insert_new_edition_panels((measurement,))
        else:
            # If we were passed a dock item it means we are replacing an
            # existing measurement with a different one, so the previous one is
            # not edited anymore.
            self.plugin.edited_measurements.remove((dock_item.measurement,))
            dock_item.measurement = measurement

        self._selection_tracker.set_selected_measurement(measurement)

        # HINT: code used to track ref leak to root task
        # requires to activtae root task instance tracking in tasks.base_tasks
#        def print_infos(root):
#            import gc
#            gc.collect()
#            import inspect
#            from exopy.tasks.tasks.base_tasks import ROOTS
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
#        deferred_call(print_infos, measurement.root_task)

    # TODO : making this asynchronous or notifying the user would be super nice
    def enqueue_measurement(self, measurement):
        """Put a measurement in the queue if it pass the tests.

        Parameters
        ----------
        measurement : Measurement
            Instance of Measurement representing the measurement.

        Returns
        -------
        bool
            True if the measurement was successfully enqueued, False otherwise.

        """
        # Reset the forced enqueued flag
        measurement.forced_enqueued = False

        # Collect the runtime dependencies
        res, msg, errors = measurement.dependencies.collect_runtimes()

        if not res:
            if 'Failed' in msg:
                dial = ChecksDisplay(errors=errors, title=msg)
                dial.exec_()
                measurement.dependencies.reset()
                return False

            # If some runtime are missing let the user know about it.
            else:
                msg = ('The following runtime dependencies of the measurement '
                       '{}, are  not currently available. Some tests may be '
                       'skipped as a result but will be run before executing '
                       'the measurement.\n Missing dependencies from :\n{}')
                msg = msg.format(measurement.name,
                                 '\n'.join(('- '+id for id in errors)))
                # TODO : log as debug and display in popup
                logger.info(msg)

        # Run the checks specifying what runtimes are missing.
        missings = errors.get('unavailable', {})
        check, errors = measurement.run_checks(missing=missings)

        # Release the runtimes.
        measurement.dependencies.release_runtimes()

        if check:
            # If check is ok but there are some errors, those are warnings
            # which the user can either ignore and enqueue the measurement, or
            # he can cancel the enqueuing and try again.
            if errors:
                dial = ChecksDisplay(errors=errors, is_warning=True)
                dial.exec_()
                if not dial.result:
                    measurement.dependencies.reset()
                    return False
        else:
            measurement.dependencies.reset()
            dial = ChecksDisplay(errors=errors, is_warning=False)
            dial.exec_()
            if not dial.result:
                measurement.dependencies.reset()
                return False
            measurement.forced_enqueued = True

        default_filename = (measurement.name + '_' + measurement.id +
                            '.meas.ini')
        path = os.path.join(measurement.root_task.default_path,
                            default_filename)

        old_path = measurement.path
        measurement.save(path)
        measurement.path = old_path
        b_deps = measurement.dependencies.get_build_dependencies()

        meas, errors = Measurement.load(self.plugin, path, b_deps.dependencies)

        # Clean dependencies cache as at next enqueueing dependencies may have
        # changed
        measurement.dependencies.reset()

        # Provide a nice error message.
        if not meas:
            measurement.forced_enqueued = False
            msg = 'Failed to rebuild measurement from config'
            dial = ChecksDisplay(errors={'Building': errors}, title=msg)
            dial.exec_()
            return False

        meas.forced_enqueued = measurement.forced_enqueued

        try:
            os.remove(path)
        except OSError:
            logger.debug('Failed to remove temp save file')

        meas.status = 'READY'
        meas.infos = 'The measurement is ready to be performed by an engine.'
        self.plugin.enqueued_measurements.add(meas)

        return True

    def reenqueue_measurement(self, measurement):
        """ Mark a measurement already in queue as fitted to be executed.

        This method can be used to re-enqueue a measurement that previously
        failed, for example because a profile was missing, the measurement can
        then be edited again and will be executed in its turn.

        WARNING : the test are run again !!!

        Parameters
        ----------
        measurement : Measurement
            The measurement to re-enqueue

        """
        measurement.enter_edition_state()
        measurement.status = 'READY'
        measurement.infos = 'Measurement re-enqueued by the user'

    def remove_processed_measurements(self):
        """ Remove all the measurements which have been processed from the queue.

        This method rely on the status of the measurement. Only measurements whose
        status is 'READY' will be left in the queue.

        """
        for measurement in self.plugin.enqueued_measurements.measurements[:]:
            if measurement.status in ('SKIPPED', 'FAILED', 'COMPLETED',
                                      'INTERRUPTED'):
                self.plugin.enqueued_measurements.remove(measurement)

    def start_processing_measurements(self):
        """ Starts to perform the measurement in the queue.

        Measurement are processed in their order of appearance in the queue.

        """
        if not self._ensure_selected_engine():
            return

        measurement = self.plugin.find_next_measurement()
        self.plugin.processor.continuous_processing = True
        if measurement is not None:
            self.plugin.processor.start_measurement(measurement)
        else:
            cmd = 'exopy.app.errors.signal'
            core = self.workbench.get_plugin('enaml.workbench.core')
            msg = 'None of the curently enqueued measurements can be run.'
            core.invoke_command(cmd, {'kind': 'error', 'message': msg})

    def process_single_measurement(self, measurement):
        """ Performs a single measurement and then stops.

        Parameters
        ----------
        measurement : Measurement
            Measurement to perform.

        """
        if not self._ensure_selected_engine():
            return

        self.plugin.processor.continuous_processing = False

        self.plugin.processor.start_measurement(measurement)

    def pause_current_measurement(self):
        """Pause the currently active measurement.

        """
        self.plugin.processor.pause_measurement()

    def resume_current_measurement(self):
        """Resume the currently paused measurement.

        """
        self.plugin.processor.resume_measurement()

    def stop_current_measurement(self, no_post_exec=False, force=False):
        """Stop the execution of the currently executed measurement.

        """
        self.plugin.processor.stop_measurement(no_post_exec, force)

    def stop_processing_measurements(self, no_post_exec=False, force=False):
        """Stop processing enqueued measurement.

        """
        self.plugin.processor.stop_processing(no_post_exec, force)

    @property
    def dock_area(self):
        """ Getter for the dock_area of the content.

        """
        if self.content and self.content.children:
            return self.content.children[1]

    # --- Private API ---------------------------------------------------------

    #: Background thread determining the last edited measurement by analysing
    #: the last selected widget.
    _selection_tracker = Typed(MeasurementTracker, ())

    def _attach_default_tools(self, measurement):
        """Add the default tools to a measurement.

        """
        # TODO : use error plugin to report that kind of issues
        for pre_id in self.plugin.default_pre_hooks:
            if pre_id in self.plugin.pre_hooks:
                measurement.add_tool('pre-hook', pre_id)
            else:
                msg = "Default pre-execution hook {} not found"
                logger.warn(msg.format(pre_id))

        for monitor_id in self.plugin.default_monitors:
            if monitor_id in self.plugin.monitors:
                measurement.add_tool('monitor', monitor_id)
            else:
                msg = "Default monitor {} not found."
                logger.warn(msg.format(monitor_id))

        for post_id in self.plugin.default_post_hooks:
            if post_id in self.plugin.post_hooks:
                measurement.add_tool('post-hook', post_id)
            else:
                msg = "Default post-execution hook {} not found"
                logger.warn(msg.format(post_id))

    def _insert_new_edition_panels(self, measurements, update=True, panels=None):
        """Handle inserting a new MeasurementEditorDockItem in the content.

        """
        if panels is None:
            template = 'meas_%d'
            items = self.dock_area.dock_items()
            test = re.compile('meas\_([0-9]+)$')
            measurement_items = [i for i in items if test.match(i.name)]

            ops = []
            for measurement in measurements:
                if not measurement_items:
                    name = template % 0
                    ops.append(InsertItem(item=name, target='meas_exec'))
                else:
                    indexes = [int(test.match(i.name).group(1))
                               for i in measurement_items]
                    indexes.sort()

                    if len(indexes) <= max(indexes):
                        ind = [i for i, x in enumerate(indexes) if i != x][0]
                    else:
                        ind = len(measurement_items)

                    name = template % ind
                    ops.append(InsertTab(item=name,
                                         target=template % indexes[0]))

                measurement_items.append(
                    MeasurementEditorDockItem(self.dock_area,
                                              workspace=self,
                                              measurement=measurement,
                                              name=name)
                    )

            if update:
                deferred_call(self.dock_area.update_layout, ops)
        else:
            for m in measurements:
                if m not in panels:
                    msg = ('Cannot insert edition panels for measurement %s, '
                           'no infos were provided. Panels exists for:\n%s')
                    raise RuntimeError(msg % (m.name + ' (id : %s)' % m.id,
                                              ', '.join(m.name for m in panels)
                                              )
                                       )
                ed_name, t_name = panels[m]
                MeasurementEditorDockItem(self.dock_area, workspace=self,
                                          measurement=m, name=ed_name)
                if t_name:
                    ToolsEditorDockItem(self.dock_area, measurement=m,
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

    def _get_last_selected_measurement(self):
        """Wait for the background to finish processing the selected widgets.

        """
        return self._selection_tracker.get_selected_measurement()

    def _ensure_selected_engine(self):
        """Make sure an engine is selected and if not prompt the user to choose
        one.

        """
        if not self.plugin.selected_engine:
            dial = EngineSelector(plugin=self.plugin)
            if dial.exec_() and dial.selected_decl:
                self.plugin.selected_engine = dial.selected_decl.id

        return bool(self.plugin.selected_engine)
