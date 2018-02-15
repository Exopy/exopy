Exopy: versatile data acquisition software for complex experiments
==================================================================

.. image:: https://travis-ci.org/Exopy/exopy.svg?branch=master
    :target: https://travis-ci.org/Exopy/exopy
    :alt: Build Status
.. image:: https://codecov.io/gh/Exopy/exopy/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/Exopy/exopy
    :alt: Coverage
.. image:: https://readthedocs.org/projects/exopy/badge/?version=latest
    :target: http://exopy.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://api.codacy.com/project/badge/Grade/4f8a569506ce4187a8a7ad2f69c6b171
    :target: https://www.codacy.com/app/Exopy/exopy?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Exopy/exopy&amp;utm_campaign=Badge_Grade
    :alt: Code quality (Codacy)
.. image:: https://anaconda.org/exopy/exopy/badges/version.svg
    :target: https://anaconda.org/exopy/exopy
    :alt: Conda package


Exopy is a versatile data acquisition software. It provides an extensible set
of tools to describe an perform data acquisition. Each measurement is described
by a hierarchical structure, allowing simple nested loops structure and more
complex ones involving multiple non nested loops and conditions. The hierarchy
is edited through a Graphical User Interface, allowing a smooth learning curve.
The elementary brick used in the hierarchy is referred to as a task. Each task
can read and write values from a common data structure allowing for easy communication between tasks and a high level of custimization despite the use
of a GUI. Furthermore, one can specify at the level of each tasks if it
should be executed in a different thread and how it should behave with respect
to other tasks running in threads. The application design make it easily
customizable on a per lab basis while benefitting from a common architecture.

For more details see the documentation: http://exopy.readthedocs.io/


Installling
-----------

The easiest way to install Exopy is through conda :

.. code:: shell

    conda install exopy -c exopy
