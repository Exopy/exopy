# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the corner cases of the internal checks.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import pytest
from future.builtins import str

from exopy.tasks.api import RootTask


@pytest.fixture
def fake_meas(measure):
    """Create a measure with a dummy root_task.

    """
    class RT(RootTask):

        dep_type = 'dummy'

    measure.root_task = RT()
    return measure


def test_attempt_to_overwrite(fake_meas, tmpdir):
    """Test running the checks when the save file for the measure already
    exists.

    """
    fake_meas.name = 'test'
    fake_meas.id = '001'
    fake_meas.root_task.default_path = str(tmpdir)

    with open(str(tmpdir.join('test_001.meas.ini')), 'wb'):
        pass

    fake_meas.dependencies.collect_runtimes()
    res, err = fake_meas.run_checks()
    assert res
    assert 'exopy.internal_checks' in err


def test_fail_build_collection(fake_meas, tmpdir, monkeypatch):
    """Test running the checks on a measure whose build dep cannot be collected

    """
    fake_meas.name = 'test'
    fake_meas.id = '001'
    fake_meas.root_task.default_path = str(tmpdir)

    import enaml
    with enaml.imports():
        from exopy.testing.measure.contributions import Flags
    monkeypatch.setattr(Flags, 'BUILD_FAIL_COLLECT', True)

    fake_meas.dependencies.collect_runtimes()
    res, err = fake_meas.run_checks()
    assert not res
    assert 'exopy.internal_checks' in err
