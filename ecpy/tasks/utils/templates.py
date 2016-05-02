# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Utility function to manipulate template files.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)
from configobj import ConfigObj
from textwrap import wrap


def load_template(path):
    """ Load the informations stored in a template.

    Parameters
    ----------
        path : unicode
            Location of the template file.

    Returns
    -------
        data : ConfigObj
            The data needed to rebuild the tasks.

        doc : unicode
            The doc of the template.

    """
    config = ConfigObj(path, encoding='utf-8', indent_type='    ')
    doc_list = [com[1:].strip() for com in config.initial_comment]
    doc = '\n'.join(doc_list)

    return config, doc


def save_template(path, data, doc):
    """ Save a template to a file

    Parameters
    ----------
        path : unicode
            Path of the file to which save the template
        data : dict
            Dictionnary containing the tempate parameters
        doc : unicode
            The template doc

    """
    # Create an empty ConfigObj and set filename after so that the data are
    # not loaded. Otherwise merge might lead to corrupted data.
    config = ConfigObj(indent_type='    ', encoding='utf-8')
    config.filename = path
    config.merge(data)
    config.initial_comment = wrap(doc, 79)

    config.write()
