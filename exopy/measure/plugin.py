# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
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
from functools import partial

from atom.api import Typed, Unicode, List, ForwardTyped, Enum, Bool, Dict

from ..utils.plugin_tools import (HasPreferencesPlugin, ExtensionsCollector,
                                  make_extension_validator)
from .engines.api import Engine
from .monitors.api import Monitor
from .hooks.api import PreExecutionHook, PostExecutionHook
from .editors.api import Editor
from .processor import MeasureProcessor
from .container import MeasureContainer

logger = logging.getLogger(__name__)

ENGINES_POINT = 'exopy.measure.engines'

MONITORS_POINT = 'exopy.measure.monitors'

PRE_HOOK_POINT = 'exopy.measure.pre-execution'

POST_HOOK_POINT = 'exopy.measure.post-execution'

EDITORS_POINT = 'exopy.measure.editors'


def _workspace():
    from .workspace.workspace import MeasureSpace
    return MeasureSpace


class MeasurePlugin(HasPreferencesPlugin):
    """The measure plugin is reponsible for managing all measure related
    extensions and handling measure execution.

    """
    #: Reference to the workspace if any.
    workspace = ForwardTyped(_workspace)

    #: Reference to the last directory from/in which a measure was loaded/saved
    path = Unicode().tag(pref=True)

    #: Currently edited measures.
    edited_measures = Typed(MeasureContainer, ())

    #: Currently enqueued measures.
    enqueued_measures = Typed(MeasureContainer, ())

    #: Measure processor responsible for measure execution.
    processor = Typed(MeasureProcessor)

    #: List of currently available engines.
    engines = List()

    #: Currently selected engine represented by its id.
    selected_engine = Unicode().tag(pref=True)

    #: What to do of the engine when there is no more measure to perform.
    engine_policy = Enum('stop', 'sleep').tag(pref=True)

    #: List of currently available pre-execution hooks.
    pre_hooks = List()

    #: Default pre-execution hooks to use for new measures.
    default_pre_hooks = List().tag(pref=True)

    #: List of currently available monitors.
    monitors = List()

    #: Default monitors to use for new measures.
    default_monitors = List(default=['exopy.text_monitor']).tag(pref=True)

    #: Always show monitors on measure startup.
    auto_show_monitors = Bool(True).tag(pref=True)

    #: List of currently available post-execution hooks.
    post_hooks = List()

    #: Default post-execution hooks to use for new measures.
    default_post_hooks = List().tag(pref=True)

    #: List of currently available editors.
    editors = List()

    # TODO add the possibility to deactivate some editors.

    def start(self):
        """Start the plugin lifecycle by collecting all contributions.

        """
        core = self.workbench.get_plugin('enaml.workbench.core')
        core.invoke_command('exopy.app.errors.enter_error_gathering')

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

        checker = make_extension_validator(PreExecutionHook, ('new',))
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

        # This call is delayed till there to avoid loading the preferences
        # before discovering the contributions (would be an issue for engine).
        super(MeasurePlugin, self).start()

        state = core.invoke_command('exopy.app.states.get',
                                    {'state_id': 'exopy.app.directory'})

        m_dir = os.path.join(state.app_directory, 'measure')
        # Create measure subfolder if it does not exist.
        if not os.path.isdir(m_dir):
            os.mkdir(m_dir)

        s_dir = os.path.join(m_dir, 'saved_measures')
        # Create saved_measures subfolder if it does not exist.
        if not os.path.isdir(s_dir):
            os.mkdir(s_dir)

        if not os.path.isdir(self.path):
            self.path = s_dir

        cmd = 'exopy.app.errors.signal'
        for contrib in ('pre_hooks', 'monitors', 'post_hooks'):
            default = getattr(self, 'default_'+contrib)
            avai_default = [d for d in default
                            if d in getattr(self, contrib)]
            if default != avai_default:
                msg = 'The following {} have not been found : {}'
                missing = set(default) - set(avai_default)
                core.invoke_command(cmd, dict(kind='error',
                                              message=msg.format(contrib,
                                                                 missing)))
                setattr(self, 'default_'+contrib, avai_default)

        for contrib in ('engines', 'editors', 'pre_hooks', 'monitors',
                        'post_hooks'):
            getattr(self, '_'+contrib).observe('contributions',
                                               partial(self._update_contribs,
                                                       contrib))

        core.invoke_command('exopy.app.errors.exit_error_gathering')

    def stop(self):
        """Stop the plugin and remove all observers.

        """
        # Close the monitors window.
        if self.processor.monitors_window:
            self.processor.monitors_window.hide()
            self.processor.monitors_window.close()
            self.processor.monitors_window = None

        for contrib in ('engines', 'editors', 'pre_hooks', 'monitors',
                        'post_hooks'):
            getattr(self, '_'+contrib).stop()

    def get_declarations(self, kind, ids):
        """Get the declarations of engines/editors/tools.

        If an id does not correspond to a known declarations it will be omitted
        from the return value, but no error will be raised. This is because the
        user can easily know which declarations exist by looking at the
        appropriate member of the plugin.

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

        decls = getattr(self, '_'+kind.replace('-', '_')+'s').contributions
        return {k: v for k, v in decls.items() if k in ids}

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
        obj : BaseEngine|BaseMeasureTool|BaseEditor
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

        decls = getattr(self, '_'+kind.replace('-', '_')+'s').contributions
        if id not in decls:
            raise ValueError('Unknown {} : {}'.format(kind, id))

        return decls[id].new(self.workbench, default)

    def find_next_measure(self):
        """Find the next runnable measure in the queue.

        Returns
        -------
        measure : Measure|None
            First valid measurement in the queue or None if there is no
            available measure.

        """
        enqueued_measures = self.enqueued_measures.measures
        i = 0
        measure = None
        # Look for a measure not being currently edited. (Can happen if the
        # user is editing the second measure when the first measure ends).
        while i < len(enqueued_measures):
            measure = enqueued_measures[i]
            if measure.status != 'READY':
                i += 1
                measure = None
            else:
                break

        return measure

    # =========================================================================
    # --- Private API ---------------------------------------------------------
    # =========================================================================

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

    #: Workspace state infos kept to preserve layout.
    _workspace_state = Dict()

    def _post_setattr_selected_engine(self, old, new):
        """Ensures that the selected engine is informed when it is selected and
        deselected.

        This is always called before notifying the workspace of the change.

        """
        # Destroy old instance if any.
        self.processor.engine = None

        if old in self.engines:
            engine = self._engines.contributions[old]
            engine.react_to_unselection(self.workbench)
        if new and new in self.engines:
            engine = self._engines.contributions[new]
            engine.react_to_selection(self.workbench)

    def _update_contribs(self, name, change):
        """Update the list of available contributions (editors, engines, tools)
        when they change.

        """
        setattr(self, name, list(getattr(self, '_'+name).contributions))

    def _default_processor(self):
        """Create a MeasureProcessor with a reference to the plugin.

        """
        return MeasureProcessor(plugin=self)
