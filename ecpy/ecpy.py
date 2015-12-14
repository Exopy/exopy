# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Application startup script.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import enaml
from atom.api import Atom, Dict, Value
from enaml.workbench.api import Workbench
from past import basestring

with enaml.imports():
    from enaml.workbench.core.core_manifest import CoreManifest
    from enaml.workbench.ui.ui_manifest import UIManifest
    from ecpy.app.manifest import AppManifest
    from ecpy.app.preferences.manifest import PreferencesManifest
    from ecpy.app.state.manifest import StateManifest
    from ecpy.app.dependencies.manifest import DependenciesManifest
    from ecpy.app.errors.manifest import ErrorsManifest
    from ecpy.app.packages import PackagesManifest
    from ecpy.app.log.manifest import LogManifest
    from ecpy.measure.manifest import MeasureManifest
    from ecpy.tasks.manager.manifest import TaskManagerManifest


class ArgParser(Atom):
    """

    """
    #:
    subparsers = Dict()

    #:
    choices = Dict()

    #:
    argument_rules = Dict()

    def __init__(self):
        super(ArgParser, self).__init__()
        self.add_argument("-s", "--nocapture",
                          help="Don't capture stdout/stderr",
                          action='store_false')
        self.add_argument("-w", "--workspace",
                          help='Select start-up workspace',
                          default='measure', choices='workspaces')
        # Add defaults arguments.

    def add_argument(self, *args, **kwargs):
        """
        """
        pass
        # If choices in the kwargs and is basestring insert a ref to a list
        # that will be modified in place.

    def add_choice(self, kind, name, value):
        """
        """
        pass

    def add_subparser(self, name):
        """
        """
        pass

    def add_argument_rule(self, kwarg, action):
        """
        """
        # Need to validate kwarg
        pass

    # --- Private API ---------------------------------------------------------

    _parser = Value()

    def _default_parser(self):
        """Create a default argument parser.

        """
        import argparse
        parser = argparse.ArgumentParser(description='Start Ecpy')
        return parser


def main():
    """
    """
    # TODO implement argument adding to parser through extension points
    # Need to do that with try except and should anything bad happen store it
    # and display a warning dialog

    # Build parser from ArgParser and parse arguemnts
#    import argparse
#    parser = argparse.ArgumentParser(description='Start the Hqc app')
#    parser.add_argument("-w", "--workspace", help='select start-up workspace',
#                        default='measure', choices=WORKSPACES)
#    parser.add_argument("-s", "--nocapture",
#                        help="Don't capture stdout/stderr",
#                        action='store_false')

    try:
        args = parser.parse_args()
    except Exception:
        pass # Display message

    workbench = Workbench()
    workbench.register(CoreManifest())
    workbench.register(UIManifest())
    workbench.register(AppManifest())
    workbench.register(StateManifest())
    workbench.register(ErrorsManifest())
    workbench.register(PreferencesManifest())
    workbench.register(LogManifest())
    workbench.register(PackagesManifest())
    workbench.register(DependenciesManifest())
    workbench.register(TaskManagerManifest())
    workbench.register(MeasureManifest())

    try:
        app = workbench.get_plugin('ecpy.app')
        app.run_app_startup(args)
    except Exception:
        pass # Display error message

    core = workbench.get_plugin('enaml.workbench.core')
    workspace = parser.choices['workspace'][args.workspace]
    core.invoke_command('enaml.workbench.ui.select_workspace',
                        {'workspace': workspace}, workbench)

    ui = workbench.get_plugin(u'enaml.workbench.ui')
    ui.show_window()
    ui.window.maximize()
    ui.start_application()

    # Unregister all contributed packages
    workbench.unregister('ecpy.app.packages')

    workbench.unregister('ecpy.measure')
    workbench.unregister('ecpy.tasks')
    workbench.unregister('ecpy.app.logging')
    workbench.unregister('ecpy.app.preferences')
    workbench.unregister('ecpy.app.state')
    workbench.unregister('ecpy.app.dependencies')
    workbench.unregister('ecpy.app.errors')
    workbench.unregister('ecpy.app')
    workbench.unregister(u'enaml.workbench.ui')
    workbench.unregister(u'enaml.workbench.core')


if __name__ == '__main__':

    main()
