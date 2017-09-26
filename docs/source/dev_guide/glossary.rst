.. _dev_glossary:

.. include:: ../substitutions.sub

Glossary and principle
======================

Ecpy is built a a plugin-application. Each functionality is contributed by a
plugin which is mounted at application start-up (or later) and can be
unmounted. This adds a bit of complexity to the application but a lot of
flexibility. This section will introduce some notions and definitions which
will be used in the following of this guide.

.. contents::

Set up ecpy in developper mode
------------------------------
Here we describe a simple workflow for developpers to contribute to ecpy.  It
is convenient to use a git GUI such as smartgit. Then, create a repository on
your computer and clone all the ecpy repositories (ecpy,
ecpy_hqc_legacy, ecpy_pulses, etc). On your command terminal, navigate to the
folder of each repository, and type the following command:
    $ python setup.py develop
this install allows ecpy components to be well detected while directly taking
account any change made to the code. When you want to add a development, use
your git GUI to create a branch from master, and give it a consistent name.
When you finish your development, rebase to master, and then push your branch.
Rebasing to master makes it as if you branched off master the day you push,
which means you incorporate all the changes on master up to that day, and this
forces you to deal with potential conflicts. Note that pushing rebased branches
implies rewriting the history of the remote branch, and hence you will need to 
force push your changes. You can now open a pull request. Your code will be
discussed among the ecpy contributors, and when judged adequate, it will be
merged onto the master branch.

Note that while you are developping you can switch between various python
versions through the Anaconda environment to test your code before pushing.

Application architecture
------------------------

At the core of the application stands the workbench which is responsible for
handling the registering and unregistering of all plugins. It is through it
that one can access to a plugin. All plugins can access to the workbench
through their 'workbench' attribute.

See the Workbench in enaml.workbench.workbench.py for more details about the
capabilities of the workbench.


Structure of a plugin
---------------------

A plugin is divided into two parts:

- a manifest (subclass of |PluginManifest|) which
  is purely declarative and states what functionalities the plugin contribute
  to the application and how its own functionalities can be extended.
- an active part (subclass of |Plugin|) which implement
  the logic necessary for the new functionality provided by the plugin (such
  as the handling of the contributions to the plugin functionalities).

Most of the time, you won't need to write the active part as you will simply
contribute new capabilities to existing plugin.

The manifest of a plugin is written in an enaml file (.enaml). It must be given
an id (which must be unique and is a dot separated string, ex:
'ecpy.app.logging') and can have a two kind of children :

- |ExtensionPoint| children are used to declare points to which other plugin can
  contribute to extend the plugin capabilities. The extension point needs an
  id.
- |Extension| children are used to declare contribution to other plugins, they
  must have an id and declare to which extension point they are contributing.
  The extension point is the combination of the plugin id and the extension
  point id. The nature of the children of an extension depends on the
  extension point to which the extension contributes.

For example the 'ecpy.instruments' plugin is responsible for collecting
drivers for instruments (which can be contributed by other plugins) and
managing the access authorisation to each instrument to avoid conflict between
different part of the application.


.. note::

    The plugin architecture used in Ecpy comes from the `Enaml`_ library which
    is also used for building the graphical user interface (GUI). If you want
    to know more about the way plugins works in `Enaml`_ you can look at
    `this document`_.

.. _Enaml: http://nucleic.github.io/enaml/docs/
.. _this document: https://github.com/nucleic/enaml/blob/master/examples/workbench/crash_course.rst

Extension packages
------------------

In order to load the plugin you want to add to Ecpy the application needs a way
to detect it. To do so at start up Ecpy scan installed python packages looking
for the the following setuptools entry point : 'ecpy_package_extension', which
must point  to a function taking  no arguments. This function must return an
iterable of manifests which will be registered.

This means that whatever you want to contribute to Ecpy you must make it an
installable python package. The Ecpy organisation on `Github`_ has a dummy
`repository`_ that you can use as a template when creating your own package. It
has the basic structure you need, you simply need to change the name of the
package (in setup.py and the folder) and make the bootstrap function
found in the __init__.py file of the package return the manifests you want to
register. Once this is done the easiest way to work is to install your package
in development mode by running from the command line (from the directory of the
setup.py file) the following command :

    $ python setup.py develop

In development mode, files are not copied to the python site-packages folder
but python directly looks into the original folder when it needs them, so you
can modify them and directly see the result without re-installing anything.

.. note:

	An extension package can also contribute new command line arguments by
	adding an extension to the 'ecpy_cmdline_args' entry point. Contribution
	should be a pair (function, priority). The function will receive an
	|ArgParser| instance and can use it to add new (optional) arguments or
	choices. Choices are used to allow to add acceptable values for an
	argument. For example, '--workspace' expect a valid workspace id and the
	choices are stored in the 'workspaces' choices.

.. _Github: https://github.com/Ecpy
.. _repository: https://github.com/Ecpy/ecpy_ext_demo
