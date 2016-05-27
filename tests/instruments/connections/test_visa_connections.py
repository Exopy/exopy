# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test for the Visa connections.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

import enaml

from ecpy.testing.util import show_widget, process_app_events
with enaml.imports():
    from ecpy.instruments.connections.visa_connections\
        import (VisaRaw, VisaRS232, VisaGPIB, VisaUSB, VisaTCPIP)

try:
    from pyvisa.rname import assemble_canonical_name
except ImportError:
    assemble_canonical_name = lambda **x: True


def test_visa_raw(windows):
    """Test the raw visa connection used for aliases or unsupported resources.

    """
    c = VisaRaw()
    show_widget(c)
    c.widgets()[1].text = 'dummy'
    assert c.gather_infos() == {'resource_name': 'dummy'}


def test_visa_rs232(windows):
    """Test the rs232 visa connection.

    """
    c = VisaRS232()
    show_widget(c)
    c.widgets()[-1].text = '1'
    process_app_events()
    assert c.gather_infos() == {'interface_type': 'ASRL',
                                'resource_class': 'INSTR',
                                'board': '1'}
    assemble_canonical_name(**c.gather_infos())


def test_visa_GPIB(windows):
    """Test the GPIB visa connection.

    """
    c = VisaGPIB()
    show_widget(c)
    c.widgets()[-2].text = '1'
    process_app_events()
    c.widgets()[-1].checked = True
    process_app_events()
    assert c.gather_infos() == {'interface_type': 'GPIB',
                                'resource_class': 'INSTR',
                                'board': '0',
                                'primary_address': '1',
                                'secondary_address': '0'}
    assemble_canonical_name(**c.gather_infos())


def test_visa_usb(windows):
    """ Test the visa usb connection.

    """
    c = VisaUSB()
    show_widget(c)
    c.widgets()[-6].text = '0x00'
    c.widgets()[-4].text = '0x01'
    c.widgets()[-2].text = '0x02'
    process_app_events()
    c.widgets()[-1].checked = True
    process_app_events()
    assert c.gather_infos() == {'interface_type': 'USB',
                                'resource_class': 'INSTR',
                                'manufacturer_id': '0x00',
                                'model_code': '0x01',
                                'serial_number': '0x02',
                                'usb_interface_number': '0',
                                'board': '0'}
    assemble_canonical_name(**c.gather_infos())


def test_visa_tcpip_instr(windows):
    """Test the visa tcpip connection.

    """
    c = VisaTCPIP()
    show_widget(c)
    c.widgets()[-4].text = '192.168.0.10'
    process_app_events()
    c.widgets()[-1].checked = True
    process_app_events()
    assert c.gather_infos() == {'interface_type': 'TCPIP',
                                'resource_class': 'INSTR',
                                'host_address': '192.168.0.10',
                                'lan_device_name': '',
                                'board': '0'}
    assemble_canonical_name(**c.gather_infos())


def test_visa_tcpip_socket(windows, process_and_sleep):
    """Test the visa tcpip connection.

    """
    c = VisaTCPIP()
    show_widget(c)
    c.resource_class = 'SOCKET'
    process_and_sleep()
    c.widgets()[-4].text = '192.168.0.10'
    c.widgets()[-2].text = '10000'
    process_app_events()
    c.widgets()[-1].checked = True
    process_app_events()
    assert c.gather_infos() == {'interface_type': 'TCPIP',
                                'resource_class': 'SOCKET',
                                'host_address': '192.168.0.10',
                                'port': '10000',
                                'board': '0'}
    assemble_canonical_name(**c.gather_infos())
