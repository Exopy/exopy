Cutting release memento
=======================

Prepare the release
-------------------

- update the version number
- update the dependencies in setup.py
- run checks in a clean environment
- check that the release notes are up to date

Test source distribution
------------------------

- clean/delete the dist directory
- build the source release distribution::
    python setup.py sdist
- check the content of the created archive
- upload the package on Test PyPI using twine::
    twine upload --repository-url https://test.pypi.org/legacy/ dist/*
- test the package from PyPI, installing using::
    pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple your-package
- fix any issue that show up and re-test (from the beginning of the section)

Cut the final release
---------------------

- commit the last changes
- add a tag with the new version number
- push the tag and then push the commit 
  (this way Travis build has the proper git version)
- push the release to PyPI using twine
    twine upload dist/*


