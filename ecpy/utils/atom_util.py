# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Utility function to work with Atom tagged members and to automatize
preferences handling.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from past.builtins import basestring
from future.utils import bind_method
from collections import OrderedDict
from atom.api import Str, Unicode, Enum, Atom
from ast import literal_eval


def tagged_members(obj, meta=None, meta_value=None):
    """ Utility function to retrieve tagged members from an object

    Parameters
    ----------
    meta : str, optional
        The tag to look for, only member which has this tag will be returned

    meta_value : optional
        The value of the metadata used for filtering the members returned

    Returns
    -------
    tagged_members : dict(str, Member)
        Dictionary of the members whose metadatas corresponds to the predicate

    """
    members = obj.members()
    if meta is None and meta_value is None:
        return members
    elif meta_value is None:
        return {key: member for key, member in members.items()
                if member.metadata is not None and meta in member.metadata}
    else:
        return {key: member for key, member in members.items()
                if member.metadata is not None
                and meta in member.metadata
                and member.metadata[meta] == meta_value}


def simple_member_from_str(member, str_value):
    """ Convert a string to the right type for a non-container member.

    Parameters
    ----------
    member : Member
        Member for which the string should be converted to a value

    str_value : string
        String to convert

    Returns
    -------
    converted_value
        The converted value

    """
    # If the member type is Str or Unicode then we just take the raw value and
    # Atom will handle the casting if any for us.
    if isinstance(member, (Str, Unicode)):
        value = str_value

    elif isinstance(member, Enum) and isinstance(member.items[0], basestring):
        value = str_value

    # Otherwise, we eval it!
    else:
        value = literal_eval(str_value)

    return value


def member_from_str(member, value):
    """ Convert a string to the right type for a member.

    Does not support Instance, Typed, Subclass, etc

    Parameters
    ----------
    member : Member
        Member for which the string should be converted to a value

    str_value : string
        String to convert

    Returns
    -------
    converted_value
        The converted value

    """
    # If we get a container must check each member
    if isinstance(value, list):
        validation_mode = member.validate_mode
        if len(validation_mode) > 1:
            val_member = validation_mode[1]
            validated = [member_from_str(val_member, val)
                         for val in value]
        else:
            validated = value

    if isinstance(value, dict):
        validation_mode = member.validate_mode
        if len(validation_mode) > 2:
            key_member = validation_mode[1]
            value_member = validation_mode[2]
            validated = {member_from_str(key_member, key):
                         member_from_str(value_member, val)
                         for key, val in value.iteritems}
        else:
            validated = value
    else:
        validated = simple_member_from_str(member, value)

    return validated


class HasPrefAtom(Atom):
    """ Base class for Atom object using preferences.

    This class defines the basic functions used to build a string dict from
    the member value and to update the members from such a dict.

    """

    pass


def preferences_from_members(self):
        """ Get the members values as string to store them in .ini files.

        """
        pref = OrderedDict()
        for name in tagged_members(self, 'pref'):
            old_val = getattr(self, name)
            if issubclass(type(old_val), HasPrefAtom):
                pref[name] = old_val.preferences_from_members()
            elif isinstance(old_val, basestring):
                pref[name] = old_val
            else:
                pref[name] = repr(old_val)

        return pref


def update_members_from_preferences(self, **parameters):
    """ Use the string values given in the parameters to update the members

    This function will call itself on any tagged HasPrefAtom member.

    """
    for name, member in tagged_members(self, 'pref').iteritems():

        if name not in parameters:
            continue

        old_val = getattr(self, name)
        if issubclass(type(old_val), HasPrefAtom):
            old_val.update_members_from_preferences(**parameters[name])
        elif old_val is None:
            pass
        else:
            value = parameters[name]
            converted = member_from_str(member, value)
            setattr(self, name, converted)

bind_method(HasPrefAtom, 'preferences_from_members', 
            preferences_from_members)
bind_method(HasPrefAtom, 'update_members_from_preferences',
            update_members_from_preferences)
