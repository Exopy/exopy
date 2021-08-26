# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Application startup script.

"""
import sys
import threading
from pkg_resources import iter_entry_points
from operator import itemgetter
from argparse import ArgumentParser

import enaml
from atom.api import Atom, Dict, Value, List
from enaml.qt.qt_application import QtApplication
from enaml.workbench.api import Workbench
from exopy.utils.traceback import format_exc

with enaml.imports():
    from enaml.stdlib.message_box import MessageBox, DialogButton
    from enaml.workbench.core.core_manifest import CoreManifest
    from enaml.workbench.ui.ui_manifest import UIManifest
    from exopy.app.app_manifest import AppManifest
    from exopy.app.preferences.manifest import PreferencesManifest
    from exopy.app.states.manifest import StateManifest
    from exopy.app.dependencies.manifest import DependenciesManifest
    from exopy.app.errors.manifest import ErrorsManifest
    from exopy.app.icons.manifest import IconManagerManifest
    from exopy.app.packages.manifest import PackagesManifest
    from exopy.app.log.manifest import LogManifest
    from exopy.app.headless.manifest import HeadlessManifest
    from exopy.measurement.manifest import MeasureManifest
    from exopy.measurement.monitors.text_monitor.manifest\
        import TextMonitorManifest
    from exopy.instruments.manifest import InstrumentManagerManifest
    from exopy.tasks.manifest import TasksManagerManifest


def setup_thread_excepthook():
    """
    Workaround for `sys.excepthook` thread bug from:
    http://bugs.python.org/issue1230540

    Call once from the main thread before creating any threads.
    """

    init_original = threading.Thread.__init__

    def init(self, *args, **kwargs):
        """Modify the run method to use sys.excepthook.

        """
        init_original(self, *args, **kwargs)
        run_original = self.run

        def run_with_except_hook(*args2, **kwargs2):
            """Call sys.excepthook if any error occurs in the thread.

            """
            try:
                run_original(*args2, **kwargs2)
            except Exception:  # pragma: no cover
                sys.excepthook(*sys.exc_info())  # pragma: no cover

        self.run = run_with_except_hook

    threading.Thread.__init__ = init


class ArgParser(Atom):
    """Wrapper class around argparse.ArgumentParser.

    This class allow to defer the actual creation of the parser and can hence
    be used to modify some arguments (choices) before creating the real parser.

    """
    #: Mappping between a name passed to the 'choices' arguments of add
    #: add_argument to allow to modify the choices after adding the argument.
    choices = Dict()

    def parse_args(self, args=None):
        """Parse the arguments.

        By default the arguments passed on the command line are parsed.

        """
        if not self._parser:
            self._init_parser()
        args = self._parser.parse_args(args)

        # Resolve choices.
        mapping = self._arg_to_choices
        for k, v in vars(args).items():
            if k in mapping:
                setattr(args, k, mapping[k][v])

        return args

    def add_argument(self, *args, **kwargs):
        """Add an argument to the parser.

        See argparse documentation for the accepted arguments and their
        meaning.

        """
        if not args[0].startswith('-'):
            raise ValueError('Only optional arguments can be added to Exopy')

        if len(args) == 1:
            arg_name = args[0].strip('--')
        else:
            arg_name = args[1].strip('--')

        if 'choices' in kwargs and kwargs['choices'] in self.choices:
            kwargs['choices'] = self.choices[kwargs['choices']]
            self._arg_to_choices[arg_name] = kwargs['choices']
            # TODO make help explain to what each value is mapped
        self._arguments.append((args, kwargs))

    def add_choice(self, kind, value, alias=None):
        """Add a possible value for a choice.

        Parameters
        ----------
        kind : unicode
            Choice id to which to add the proposed value.

        value : unicode
            New possible value to add to the list of possible value.

        alias : unicode | None
            Short name to give to the choice. If the chosen one is in conflic
            with an existing name it is ignored.

        """
        if kind not in self.choices:
            self.choices[kind] = {}

        ch = self.choices[kind]
        if not alias or alias in ch:
            ch[value] = value
        else:
            ch[alias] = value

    # --- Private API ---------------------------------------------------------

    # Cached value of the argparser.ArgumentParser instance created by
    # _init_parser, or parser provided by the parent parser.
    _parser = Value()

    # List of tuple to use to create arguments.
    _arguments = List()

    #: Mapping between argument and associated choices.
    #: Used to resolve choices.
    _arg_to_choices = Dict()

    def _init_parser(self):
        """Initialize the underlying argparse.ArgumentParser.

        """
        if not self._parser:
            self._parser = ArgumentParser()

        for args, kwargs in self._arguments:
            self._parser.add_argument(*args, **kwargs)


def display_startup_error_dialog(text, content, details=''):
    """Show a nice dialog showing to the user what went wrong during
    start up.

    """
    if not QtApplication.instance():
        QtApplication()  # pragma: no cover
    dial = MessageBox()
    dial = MessageBox(title='Exopy failed to start',
                      text=text, content=content, details=details,
                      buttons=[DialogButton(str('Close'), str('reject'))])
    dial.exec_()
    sys.exit(1)


def main(cmd_line_args=None):
    """Main entry point of the Exopy application.

    """
    # Build parser from ArgParser and parse arguemnts
    parser = ArgParser()
    parser.add_choice('workspaces', 'exopy.measurement.workspace',
                      'measurement')
    parser.add_argument("-s", "--nocapture",
                        help="Don't capture stdout/stderr",
                        action='store_true')
    parser.add_argument("-w", "--workspace",
                        help='Select start-up workspace',
                        default='measurement', choices='workspaces')
    parser.add_argument("-r", "--reset-app-folder",
                        help='Reset the application startup folder.',
                        action='store_true')
    parser.add_argument("--measurement-execute",
                        help="Execute given measurement file")

    modifiers = []
    for i, ep in enumerate(iter_entry_points('exopy_cmdline_args')):

        try:
            modifier, priority = ep.load(require=False)
            modifiers.append((ep, modifier, priority, i))
        except Exception as e:
            text = 'Error loading extension %s' % ep.name
            content = ('The following error occurred when trying to load the '
                       'entry point {} :\n {}'.format(ep.name, e))
            details = format_exc()
            display_startup_error_dialog(text, content, details)

    modifiers.sort(key=itemgetter(1, 2))
    try:
        for m in modifiers:
            m[1](parser)
    except Exception as e:
        text = 'Error modifying cmd line arguments'
        content = ('The following error occurred when the entry point {} '
                   'tried to add cmd line options :\n {}'.format(ep.name, e))
        details = format_exc()
        display_startup_error_dialog(text, content, details)

    try:
        args = parser.parse_args(cmd_line_args)
    except BaseException as e:
        if e.args == (0,):
            sys.exit(0)
        text = 'Failed to parse cmd line arguments'
        content = ('The following error occurred when trying to parse the '
                   'command line arguments :\n {}'.format(e))
        details = format_exc()
        display_startup_error_dialog(text, content, details)

    # Patch Thread to use sys.excepthook
    setup_thread_excepthook()

    workbench = Workbench()
    workbench.register(CoreManifest())
    workbench.register(UIManifest())
    workbench.register(AppManifest())
    workbench.register(StateManifest())
    workbench.register(ErrorsManifest())
    workbench.register(PreferencesManifest())
    workbench.register(IconManagerManifest())
    workbench.register(LogManifest())
    workbench.register(PackagesManifest())
    workbench.register(DependenciesManifest())
    workbench.register(InstrumentManagerManifest())
    workbench.register(TasksManagerManifest())
    workbench.register(MeasureManifest())
    workbench.register(TextMonitorManifest())
    workbench.register(HeadlessManifest())

    ui = workbench.get_plugin(u'enaml.workbench.ui')  # Create the application

    try:
        app = workbench.get_plugin('exopy.app')
        app.run_app_startup(args)
    except Exception as e:
        text = 'Error starting plugins'
        content = ('The following error occurred when executing plugins '
                   'application start ups :\n {}'.format(e))
        details = format_exc()
        display_startup_error_dialog(text, content, details)

    # Quit hard and early if we are headless mode
    if args.measurement_execute:
        return

    core = workbench.get_plugin('enaml.workbench.core')

    # Install global except hook.
    if not args.nocapture:
        core.invoke_command('exopy.app.errors.install_excepthook', {})

    # Select workspace
    core.invoke_command('enaml.workbench.ui.select_workspace',
                        {'workspace': args.workspace}, workbench)

    ui = workbench.get_plugin(u'enaml.workbench.ui')
    ui.show_window()
    ui.window.maximize()
    ui.start_application()

    core.invoke_command('enaml.workbench.ui.close_workspace',
                        {}, workbench)

    # Unregister all contributed packages
    workbench.unregister('exopy.app.packages')
    workbench.unregister('exopy.app.headless')
    workbench.unregister('exopy.measurement.monitors.text_monitor')
    workbench.unregister('exopy.measurement')
    workbench.unregister('exopy.tasks')
    workbench.unregister('exopy.instruments')
    workbench.unregister('exopy.app.icons')
    workbench.unregister('exopy.app.preferences')
    workbench.unregister('exopy.app.states')
    workbench.unregister('exopy.app.dependencies')
    workbench.unregister('exopy.app.errors')
    workbench.unregister('exopy.app.logging')
    workbench.unregister('exopy.app')
    workbench.unregister(u'enaml.workbench.ui')
    workbench.unregister(u'enaml.workbench.core')


if __name__ == '__main__':

    main()  # pragma: no cover
