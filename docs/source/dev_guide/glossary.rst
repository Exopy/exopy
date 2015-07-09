.. _dev_glossary:

.. include:: substitutions.rst

Glossary and principle
======================

Ecpy is built a a plugin-application. Each functionality is contributed by a
plugin which is mounted at application start-up (or later) and can be
unmounted. This adds a bit of complexity to the application but a lot of
flexibility. This section will introduce some notions and definitions which
will be used in the following of this guide.

..contents::


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


**Note**

The plugin architecture used in Ecpy comes from the `Enaml`_ library which is
also used for building the graphical user interface. If you want to know more
about the way plugins works in `Enaml`_ you can look at `this document`_.

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
repository that you can use as a template when creating your own package. It
has the basic structure you need, you simply need to change the name of the
package (in setup.py and the folder) and make the bootstrap function
found in the __init__.py file of the package return the manifests you want to
register. Once this is done the easiest way to work is to install your package
in development mode by running from the command line (from the directory of the
setup.py file) the following command :

	$ python setup.py development

In development mode, files are not copied to the python site-packages folder
but python directly looks into the original folder when it needs them, so you
can modify them and directly see the result without re-installing anything.

.. _Github: https://github.com/Ecpy
