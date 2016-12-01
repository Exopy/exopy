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

from collections import OrderedDict
from ast import literal_eval

from textwrap import fill
from future.utils import raise_from
from past.builtins import basestring
from future.utils import bind_method
from atom.api import Str, Unicode, Enum, Atom, Constant

from inspect import getargspec
from inspect import cleandoc

# String identifing the preference tag
PREF_KEY = 'pref'
# Position in the list for the to pref and from pref methods
TO_PREF_ID = 0
FROM_PREF_ID = 1


def tagged_members(obj, meta=None, meta_value=None):
    """ Utility function to retrieve tagged members from an object

    Parameters
    ----------
    obj : Atom
        Object from which the tagged members should be retrieved.

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
                if member.metadata is not None and
                meta in member.metadata and
                member.metadata[meta] == meta_value}


def member_from_pref(obj, member, val):
    """ Retrieve the value stored in the preferences for a member.

    Parameters
    ----------
    obj : Atom
        Object who owns the member.

    member : Member
        Member for which the preferences should be retrieved.

    val : Value
        Value that is stored in the preferences, depending on the case this
        might be a serialized value or simply a string.

    Returns
    -------
    value : Value
        The deserialized value that can be assigned to the member.

    """
    meta_value = member.metadata[PREF_KEY]

    # If 'pref=True' then we rely on the standard save mechanism
    if meta_value is True:
        # If the member is a subclass of Str, Unicode then we just take the
        # raw value and Atom will handle the casting if any for us.
        # If it is a subclass of basestring then we save it as-is
        if isinstance(member, (Str, Unicode)):
            value = val

        # If it is an Enum where the first item is a (subclass of) string, then
        # we assume that the whole Enum contains strings and we save it as-is
        elif isinstance(member, Enum) and isinstance(member.items[0],
                                                     basestring):
            value = val

        # Otherwise, we eval it, or we might throw an error
        else:
            try:
                value = literal_eval(val)
            except ValueError:
                # Silently ignore failed evaluation as we can have a string
                # assigned to a value.
                value = val

    # If the user provided a custom "from_pref" function, then we check
    # that it has the correct signature and use it to obtain the value
    elif (isinstance(meta_value, (tuple, list)) and
            len(getargspec(meta_value[FROM_PREF_ID])[0]) == 3):
        value = meta_value[FROM_PREF_ID](obj, member, val)

    elif meta_value is False:
        raise NotImplementedError(
            fill(cleandoc('''you set 'pref=False' for this member. If you did
            not want to save it you should simply not declare this tag.''')))
    else:
        raise NotImplementedError(
            fill(cleandoc('''the 'pref' tag of this member was not set to true,
            therefore the program expects you to declare two functions,
             'member_to_pref(obj,member,val)' and 'member_from_pref(obj,member,
             val)' that will handle the serialization and deserialization of
             the value. Those should be passed as a list or a tuple, where
             the first element is member_to and the second is member_from.
             It is possible that you failed to properly declare the signature
             of those two functions.''')))

    return value


def member_to_pref(obj, member, val):
    """ Provide the value that will be stored in the preferences for a member.

    Parameters
    ----------
    obj : Atom
        Object who owns the member.

    member : Member
        Member for which the preferences should be retrieved

    val : Value
        Value of the member to be stored in the preferences

    Returns
    -------
    pref_value : str
        The serialized value/string that will be stored in the pref.

    """
    meta_value = member.metadata[PREF_KEY]

    # If 'pref=True' then we rely on the standard save mechanism
    if meta_value is True:
        # If val is string-like, then we can simply cast it and rely on
        # python/Atom default methods.
        if isinstance(val, basestring):
            pref_value = val
        else:
            pref_value = repr(val)

    # If the user provided a custom "to_pref" function, then we check
    # that it has the correct signature and use it to obtain the value
    elif (isinstance(meta_value, (tuple, list)) and
            len(getargspec(meta_value[TO_PREF_ID])[0]) == 3):
        pref_value = meta_value[TO_PREF_ID](obj, member, val)

    elif meta_value is False:
        raise NotImplementedError(
            fill(cleandoc('''you set 'pref=False' for this member. If you did
            not want to save it you should simply not declare this tag.''')))
    else:
        raise NotImplementedError(
            fill(cleandoc('''the 'pref' tag of this member was not set to true,
            therefore the program expects you to declare two functions,
             'member_to_pref(obj,member,val)' and 'member_from_pref(obj,member,
             val)' that will handle the serialization and deserialization of
             the value. Those should be passed as a list or a tuple, where
             the first element is member_to and the second is member_from.
             It is possible that you failed to properly declare the signature
             of those two functions.''')))

    return pref_value


def ordered_dict_to_pref(obj, member, val):
    """ Function to convert an OrderedDict to something that can
     be easily stored and read back, in this case a list of tuples.

    Parameters
    ----------
    obj: Atom
        The instance calling the function
    member: Member
        The member that must be stored
    val: OrderedDict
        The current value of the member

    Returns
    -------
    value : str
        the serialized value

    """
    return repr(list(val.items()))


def ordered_dict_from_pref(obj, member, val):
    """Read back the list of tuples saved by 'ordered_dict_to_pref'.

    We simply do a literal_eval of the list of tuples, and then convert it to
    an OrderedDict.

    Parameters
    ----------
    obj: Atom
        The instance calling the function
    member: Member
        The member that must be stored
    val: str
        The string representation of the stored value

    Returns
    -------
    value : OrderedDict
        An Ordered Dict that can be assigned to the member.

    """
    return OrderedDict(literal_eval(val))


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
    for name, member in tagged_members(self, 'pref').items():
        old_val = getattr(self, name)
        if issubclass(type(old_val), HasPrefAtom):
            pref[name] = old_val.preferences_from_members()
        else:
            pref[name] = member_to_pref(self, member, old_val)
    return pref


def update_members_from_preferences(self, parameters):
    """ Use the string values given in the parameters to update the members

    This function will call itself on any tagged HasPrefAtom member.

    """
    for name, member in tagged_members(self, 'pref').items():

        if name not in parameters or isinstance(member, Constant):
            continue

        old_val = getattr(self, name)
        if issubclass(type(old_val), HasPrefAtom):
            old_val.update_members_from_preferences(parameters[name])
        # This is meant to prevent updating fields which expect a custom
        # instance
        elif old_val is None:
            pass
        else:
            value = parameters[name]
            converted = member_from_pref(self, member, value)
            try:
                setattr(self, name, converted)
            except Exception as e:
                msg = 'An exception occured when trying to set {} to {}'
                raise_from(ValueError(msg.format(name, converted)), e)

bind_method(HasPrefAtom, 'preferences_from_members',
            preferences_from_members)
bind_method(HasPrefAtom, 'update_members_from_preferences',
            update_members_from_preferences)
