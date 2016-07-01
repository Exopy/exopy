# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""False driver to test the declarator.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)


class FalseDriver(object):
    """False driver to test the declarator.

    """
    pass


class FalseDriver2(object):
    """False driver to test the declarator.

    """
    pass


class FalseDriver3(object):
    """False driver to test the declarator.

    """
    pass


class FalseDriver4(object):
    """False driver to test the declarator.

    """
    pass


class FalseDriver5(object):
    """False driver to test the declarator.

    """
    pass


class FalseDriver6(object):
    """False driver to test the declarator.

    """
    pass


class DummyStarter(object):
    """Dummy starter for testing purposes.

    """
    def start(driver, connection, settings):
        pass

    def check_infos(driver, connection, settings):
        return True, ''

    def reset(driver):
        pass

    def stop(driver):
        pass
