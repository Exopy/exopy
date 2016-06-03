#!/bin/bash

$PYTHON setup.py install --single-version-externally-managed --record=/dev/null

rm $PREFIX/bin/easy_*
