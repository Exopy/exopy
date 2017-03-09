python setup.py install --single-version-externally-managed --record=NUL
if errorlevel 1 exit 1

del %SCRIPTS%\enaml-run.exe*
if errorlevel 1 exit 1
