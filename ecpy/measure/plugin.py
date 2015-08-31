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
from functools import partial

from atom.api import Typed, Unicode, List, ForwardTyped, Enum

from ..utils.plugin_tools import (HasPrefPlugin, ExtensionsCollector,
                                  make_extension_validator)
from .engines import Engine
from .monitors import Monitor
from .hooks import PreExecutionHook, PostExecutionHook
from .editors import Editor
from .processor import MeasureProcessor
from .container import MeasureContainer

logger = logging.getLogger(__name__)

ENGINES_POINT = 'ecpy.measure.engines'

MONITORS_POINT = 'ecpy.measure.monitors'

PRE_HOOK_POINT = 'ecpy.measure.pre-execution'

POST_HOOK_POINT = 'ecpy.measure.post-execution'

EDITORS_POINT = 'ecpy.measure.editors'


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
    edited_measures = Typed(MeasureContainer, ())

    #: Currently enqueued measures.
    enqueued_measures = Typed(MeasureContainer, ())

    #: Measure processor responsible for measure execution.
    processor = Typed(MeasureProcessor, ())

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
    default_monitors = List().tag(pref=True)

    #: List of currently available post-execution hooks.
    post_hooks = List()

    #: Default post-execution hooks to use for new measures.
    default_hooks = List().tag(pref=True)

    #: Dict holding the contributed Editor declarations
    editors = List()

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

    def check_for_dependencies_errors(self, measure, deps):
        """Check that the collection of dependencies occurred without errors.

        Parameters
        ----------
        measure : Measure
            Measure whose dependencies have been collected.

        deps : BuildContainer, RuntimeContainer
            Dependencies container.

        Returns
        -------
        result : bool
            Boolean indicating if everything was ok or not.

        reason : {None, 'errors', 'unavailable'}
            Reason for the failure if any.

        """
        core = self.workbench.get_plugin('enaml.workbench.core')
        kind = 'runtime' if hasattr(deps, 'unavailable') else 'build'
        cmd = 'ecpy.app.errors.signal'
        if deps.errors:
            msg = 'Failed to get some %s dependencies for measure %s'
            core.invoke_command(cmd, {'kind': 'measure-error',
                                      'message': msg % (kind, measure.name),
                                      'errors': deps.errors})

            return False, 'errors'

        if getattr(deps, 'unavailable', None):
            msg = ('The following runtime dependencies of measure %s are '
                   'unavailable :\n')
            msg += '\n'.join('- %s' % u for u in deps.unavailable)
            core.invoke_command(cmd, {'kind': 'error',
                                      'message': msg % measure.name})

            return False, 'unavailable'

        store_key = 'build_deps' if kind == 'build' else 'runtime_deps'
        measure.store[store_key] = deps.dependencies

        return True, None

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
        """Update the list of available contributions (editors, engines, tools)
        when they change.

        """
        setattr(self, name, list(getattr(self, '_'+name).contributions))
