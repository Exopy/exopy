# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the Visa connections.

"""
import logging

import enaml
import pytest

from exopy.testing.util import show_widget, wait_for_destruction
with enaml.imports():
    from exopy.instruments.connections.visa_connections\
        import (VisaRaw, VisaRS232, VisaGPIB, VisaUSB, VisaTCPIP,
                VisaConnection)

try:
    from pyvisa.rname import assemble_canonical_name
except ImportError:
    assemble_canonical_name = lambda **x: True


def test_visa_raw(exopy_qtbot):
    """Test the raw visa connection used for aliases or unsupported resources.

    """
    c = VisaRaw()
    show_widget(exopy_qtbot, c)
    c.widgets()[1].text = 'dummy'
    assert c.gather_infos() == {'resource_name': 'dummy'}


def test_visa_rs232(exopy_qtbot):
    """Test the rs232 visa connection.

    """
    c = VisaRS232()
    show_widget(exopy_qtbot, c)
    c.widgets()[-1].text = '1'

    def assert_infos():
        assert c.gather_infos() == {'interface_type': 'ASRL',
                                    'resource_class': 'INSTR',
                                    'board': '1'}
    exopy_qtbot.wait_until(assert_infos)
    assemble_canonical_name(**c.gather_infos())


def test_visa_GPIB(exopy_qtbot):
    """Test the GPIB visa connection.

    """
    c = VisaGPIB()
    show_widget(exopy_qtbot, c)
    c.widgets()[-2].text = '1'
    exopy_qtbot.wait(10)
    c.widgets()[-1].checked = True

    def assert_infos():
        assert c.gather_infos() == {'interface_type': 'GPIB',
                                    'resource_class': 'INSTR',
                                    'board': '0',
                                    'primary_address': '1',
                                    'secondary_address': '0'}
    exopy_qtbot.wait_until(assert_infos)
    assemble_canonical_name(**c.gather_infos())


def test_visa_usb(exopy_qtbot):
    """ Test the visa usb connection.

    """
    c = VisaUSB()
    show_widget(exopy_qtbot, c)
    c.widgets()[-6].text = '0x00'
    c.widgets()[-4].text = '0x01'
    c.widgets()[-2].text = '0x02'
    exopy_qtbot.wait(10)
    c.widgets()[-1].checked = True

    def assert_infos():
        assert c.gather_infos() == {'interface_type': 'USB',
                                    'resource_class': 'INSTR',
                                    'manufacturer_id': '0x00',
                                    'model_code': '0x01',
                                    'serial_number': '0x02',
                                    'usb_interface_number': '0',
                                    'board': '0'}
    exopy_qtbot.wait_until(assert_infos)
    assemble_canonical_name(**c.gather_infos())


def test_visa_tcpip_instr(exopy_qtbot):
    """Test the visa tcpip connection.

    """
    c = VisaTCPIP()
    show_widget(exopy_qtbot, c)
    c.widgets()[-4].text = '192.168.0.10'
    exopy_qtbot.wait(10)
    c.widgets()[-1].checked = True

    def assert_infos():
        assert c.gather_infos() == {'interface_type': 'TCPIP',
                                    'resource_class': 'INSTR',
                                    'host_address': '192.168.0.10',
                                    'lan_device_name': 'inst0',
                                    'board': '0'}
    exopy_qtbot.wait_until(assert_infos)
    assemble_canonical_name(**c.gather_infos())


def test_visa_tcpip_socket(exopy_qtbot, dialog_sleep):
    """Test the visa tcpip connection.

    """
    c = VisaTCPIP()
    show_widget(exopy_qtbot, c)
    c.resource_class = 'SOCKET'
    exopy_qtbot.wait(10 + dialog_sleep)
    c.widgets()[-4].text = '192.168.0.10'
    c.widgets()[-2].text = '10000'
    exopy_qtbot.wait(10)
    c.widgets()[-1].checked = True

    def assert_infos():
        assert c.gather_infos() == {'interface_type': 'TCPIP',
                                    'resource_class': 'SOCKET',
                                    'host_address': '192.168.0.10',
                                    'port': '10000',
                                    'board': '0'}
    exopy_qtbot.wait_until(assert_infos)
    assemble_canonical_name(**c.gather_infos())


def test_creating_a_visa_connection(prof_plugin, exopy_qtbot, caplog):
    """Test creating a Visa connection through VisaConnection.new

    """
    caplog.set_level(logging.INFO)
    c = prof_plugin.create_connection('VisaTCPIP', {'__junk': ''}, True)
    w = show_widget(exopy_qtbot, c)
    assert caplog.records
    assert c.read_only
    w.close()
    wait_for_destruction(exopy_qtbot, w)


@pytest.mark.parametrize('id, defaults, should_log',
                         [('VisaRaw',
                           {'resource_name': 'COM1'},
                           False),
                          ('VisaRaw',
                           {'resource_name': 'COM1',
                            'bad': 1},
                           True),
                          ('VisaRS232',
                           {'interface_type': 'ASRL',
                            'resource_class': 'INSTR',
                            'board': 1},
                           False),
                          ('VisaRS232',
                           {'interface_type': 'ASRL',
                            'resource_class': 'INSTR',
                            'board': 1, 'bad': 1},
                           True),
                          ('VisaGPIB',
                           {'interface_type': 'GPIB',
                            'resource_class': 'INSTR',
                            'board': 0,
                            'primary_address': 1,
                            'secondary_address': 0},
                           False),
                          ('VisaGPIB',
                           {'interface_type': 'GPIB',
                            'resource_class': 'INSTR',
                            'board': 0,
                            'primary_address': 1,
                            'secondary_address': 0,
                            'bad': 1},
                           True),
                          ('VisaUSB',
                           {'interface_type': 'USB',
                            'resource_class': 'INSTR',
                            'manufacturer_id': '0x00',
                            'model_code': '0x01',
                            'serial_number': '0x02',
                            'usb_interface_number': 0,
                            'board': 0},
                           False),
                          ('VisaUSB',
                           {'interface_type': 'USB',
                            'resource_class': 'INSTR',
                            'manufacturer_id': '0x00',
                            'model_code': '0x01',
                            'serial_number': '0x02',
                            'usb_interface_number': 0,
                            'board': 0,
                            'bad': 1},
                           True),
                          ('VisaTCPIP',
                           {'interface_type': 'TCPIP',
                            'resource_class': 'INSTR',
                            'host_address': '192.168.0.10',
                            'lan_device_name': 'inst0',
                            'port': 8000,
                            'board': 0},
                           False),
                          ('VisaTCPIP',
                           {'interface_type': 'TCPIP',
                            'resource_class': 'INSTR',
                            'host_address': '192.168.0.10',
                            'lan_device_name': 'inst0',
                            'board': 0,
                            'port': 8000,
                            'bad': 1},
                           True),
                          ('VisaTCPIP',
                           {'interface_type': 'TCPIP',
                            'resource_class': 'SOCKET',
                            'host_address': '192.168.0.10',
                            'port': 8000,
                            'lan_device_name': 'inst0',
                            'board': 0},
                           False),
                          ('VisaTCPIP',
                           {'interface_type': 'TCPIP',
                            'resource_class': 'SOCKET',
                            'host_address': '192.168.0.10',
                            'port': 8000,
                            'lan_device_name': 'inst0',
                            'bad': 0},
                           True)   ])
def test_validating_connection_default(id, defaults, should_log,
                                       exopy_qtbot, caplog, prof_plugin):
    """Test that keyword filtering works as expected.

    """
    caplog.set_level(logging.INFO)
    c = prof_plugin.create_connection(id, defaults, False)
    w = show_widget(exopy_qtbot, c)
    if should_log:
        assert caplog.records
    else:
        assert not caplog.records
    assert not c.read_only
    w.close()
    wait_for_destruction(exopy_qtbot, w)
