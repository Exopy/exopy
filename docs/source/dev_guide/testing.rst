.. _dev_testing:

.. include:: ../substitutions.sub

Writing and running tests
=========================

Unit tests are one of the few ways to discover bugs beforehand and to prevent
regressions when updating the code base. Ecpy aims at being covered at 100%
(meaning that tests must run every single line of code at least once). Coverage
is not always a perfect metric as it is not because a line does not crash that
the code does what it is meant to but it is a good indicator. Actually GUI
elements written in Enaml are not tracked by the coverage, BUT they should be
tested nonetheless.

.. note::

    The test suite is not distributed with pip packages or conda packages as it
    is solely a developing tool. However some tools used in testing and that
    may be useful to other packages can be found under the 'testing' package.

.. note::

    Running the test suite requires :

    - pytest
    - pytest-capturelog
    - pytest-cov
    - pytest-timeout
    - enaml_coverage_plugin
      (https://github.com/MatthieuDartiailh/enaml_coverage_plugin)

.. contents::


Writing test using pytest
-------------------------

The library used for writing the tests for Ecpy is pytest. Writing a test is as
easy as creating a module whose name starts by 'test\_' and inside write
functions themselves prefixed by 'test\_'. Inside a test function the correct
behaviour of the program should be tested (using assertions as described in the
next section). Test should focus on testing elementary operation at the highest
level possible (avoiding direct access to private methods is likely to make the
test easier to maintain if the code changes, note that this however not always
possible).

Assertions
^^^^^^^^^^

Python provides the 'assert' statement to check that a boolean is True. Usually
one should provide also an error message describing why the assertion failed.
One very interesting feature of pytest is that it can analyse assertions and
provide automatically detailed error reporting in case of failure.

So testing a function which should return one is as easy as :

.. code-block:: python

    def test_my_function():

        assert my_function() == 100%

Sometimes a function should raise an exception in a given situation and it
might desirable to check that it indeed do so. Pytest provides a context
handler to handle this case.

.. code-block:: python

    def test_my_other_function():

        with pytest.raises(ValueError):
            my_other_funtion(-1)

Another case which often arises in Ecpy if the need to handle a dialog opened
by the function. To handle this case one can use the |handle_dialog| context
manager found in 'ecpy.testing.util' (note a bunch of other useful function
are defined in this module):

.. code-block:: python

    def my_function_dialog():

        def handler(dialog):
            # Do something with the dialog
            pass

        with handle_dialog('accept', handler):
            my_function_dialog()

The first argument indicates whether to accept or reject the dialog, and the
second allows to modify the attributes of the dialog. Both arguments are
optional.


Fixtures
^^^^^^^^

Usually when testing the methods of an object, all tests have in common some
initialisation steps and sometimes also some finalisation steps to clean up
after the tests.

To avoid duplicating a lot of code Pytest provides fixture functions. A fixture
function is imply a function decorated with '@pytest.fixture' (or
'@pytest.yield_fixture') which, when passed as argument of a test function,
will be called automatically by pytest. Standard fixture simply gives access to
a value, yield_fixture allow to cleanup after the test execution. Note that a
fixture can rely on another fixture.

.. code-block:: python

    @pytest.fixture
    def tool():
        return 1

    @pytest.yield_fixture
    def clean_tool(tool):
        yield tool  # This will pass 1 to the test function
        del tool  # This is executed after the test function (no matter the errors)

    def test_my_function(clean_tool):
        assert clean_tool == 1

Pytest provides some useful fixtures :

- monkeypatch : an object with a setattr method to modify some code and be sure
  theat the modification will be removed before running the next text.
- tmpdir : a temporary directory (should be converted to unicode before passing
  it to 'os' module functions)

Ecpy add some other :

- app : fixture ensuring that the Application is running (mandatory for testing
  widgets).
- windows : fixtures closing all opened windows after a test.
- app_dir : return the automatically set path for the application
- dialog_sleep : return the time to sleep as specified by the --ecpy-sleep
  option

The other fixtures can be found in the testing package. Each subpackage usually
defining a fixture.py module in which those are defined.

If a fixture need to be available in multiple test module it can be defined in
a conftest.py module inside the package. If the fixture can be of use to other
packages it should be defined in a fixtures.py module inside the testing
package.

.. note::

    If a fixture is defined in a fixtures.py module, one should add a
    'pytest_plugin' variable at the top of the test module with a list of all
    the module containing fixtures to load (modules should be specified using
    their full path).

    ex : pytest_plugins = [str('ecpy.testing.instruments.fixtures')]

.. note::

    More details about fixtures can be found in the pytest `documentation_`

    .. _documentation: http://pytest.org/latest/contents.html#


Running the test suite
----------------------

To run the test suite, one should invoke pytest from the command line. First
the command line should be made to point at the root of the 'ecpy' folder
(containing both the 'ecpy' and the 'tests' packages). Then one can invoke
pytest using the 'py.test tests' command.

To run only tests linked to a limited part of the application one can specify
the path of the packages containing the tests or even the module.

>>> py.test tests/measure/monitors

To run only a single function one should specify specify its name after the
name of the module and separate them using '::'.

>>> py.test tests/measure/test_measure.py::test_tool_handling

Of course pytest can take command line arguments, please refer to the pytest
`documentation_` for more details.

Currently, Ecpy add a single argument '--ecpy-sleep' which fix the time return
by the dialog_sleep feature and can hence allow to visually test GUI elements.

    .. _documentation: http://pytest.org/latest/contents.html#

Checking coverage
^^^^^^^^^^^^^^^^^

Checking coverage is just a matter of invoking pytest with the right arguments.
First one should specify the packages/modules whose coverage should be
monitored. This is done using the '--cov' argument as follow :

>>> py.test tests --cov ecpy

By default the format under which coverage is reported is not extremely useful,
so one should specify '--cov-report' to be either 'term-missing' (that will
list the line not covered by the tests in the console) or 'html' which will
produce a report in html which can be access by opening the created index.html
file.

>>> py.test tests --cov ecpy --cov-report term-missing
