#!/bin/bash

$PYTHON setup.py install --single-version-externally-managed --record=/dev/null --no-compile

rm $PREFIX/bin/easy_*
