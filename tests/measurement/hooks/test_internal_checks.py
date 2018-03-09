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
import pytest

from exopy.tasks.api import RootTask


@pytest.fixture
def fake_meas(measurement):
    """Create a measurement with a dummy root_task.

    """
    class RT(RootTask):

        dep_type = 'dummy'

    measurement.root_task = RT()
    return measurement


def test_attempt_to_overwrite(fake_meas, tmpdir):
    """Test running the checks when the save file for the measurement already
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
    assert 'duplicate' in err['exopy.internal_checks']


def test_attempt_to_overwrite_enqueued(measurement_workbench, fake_meas,
                                       tmpdir):
    """Test running the checks when an enqueued measurement with the same name
    and id already exists.

    """
    fake_meas.name = 'test'
    fake_meas.id = '001'
    fake_meas.root_task.default_path = str(tmpdir)

    plugin = measurement_workbench.get_plugin('exopy.measurement')
    plugin.enqueued_measurements.measurements.append(fake_meas)

    fake_meas.dependencies.collect_runtimes()
    res, err = fake_meas.run_checks()
    assert res
    assert 'exopy.internal_checks' in err
    assert 'enqueued-duplicate' in err['exopy.internal_checks']


def test_fail_build_collection(fake_meas, tmpdir, monkeypatch):
    """Test running the checks on a measurement whose build dep cannot be collected

    """
    fake_meas.name = 'test'
    fake_meas.id = '001'
    fake_meas.root_task.default_path = str(tmpdir)

    import enaml
    with enaml.imports():
        from exopy.testing.measurement.contributions import Flags
    monkeypatch.setattr(Flags, 'BUILD_FAIL_COLLECT', True)

    fake_meas.dependencies.collect_runtimes()
    res, err = fake_meas.run_checks()
    assert not res
    assert 'exopy.internal_checks' in err
