# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the Atom utility functions and HasPrefAtom object.

"""
from collections import OrderedDict

import pytest
from atom.api import (Str, Float, Enum, List, Typed, Int, Value,
                      Constant)
from exopy.utils.atom_util import (tagged_members, member_from_pref,
                                   member_to_pref, HasPrefAtom,
                                   ordered_dict_from_pref,
                                   ordered_dict_to_pref)


class _Aaux(HasPrefAtom):

    int_ = Int().tag(pref=True)


class _Faux(HasPrefAtom):

    int_ = Int().tag(pref=False)


class _Aux(HasPrefAtom):

    string = Str().tag(pref=True)
    float_n = Float().tag(pref=True)
    enum = Enum('a', 'b').tag(pref=True)
    enum_float = Enum(1.0, 2.0).tag(pref=True)
    list_ = List(Float()).tag(pref=True)
    odict_ = Typed(OrderedDict, ()).tag(pref=[ordered_dict_to_pref,
                                              ordered_dict_from_pref])
    value = Value().tag(pref=True)
    const = Constant('r').tag(pref=True)

    atom = Typed(_Aaux, ()).tag(pref=True)

    no_tag = Int()


def test_false_from_pref_softerror():
    aux = _Faux()
    with pytest.raises(NotImplementedError):
        member_from_pref(aux, aux.get_member(str('int_')), 'a')


def test_false_to_pref_softerror():
    aux = _Faux()
    try:
        member_to_pref(aux, aux.get_member(str('int_')), 'a')
    except NotImplementedError:
        assert True is True


def test_tagged_members1():
    aux = _Aux()
    members = sorted(tagged_members(aux, 'pref').keys())
    test = sorted(['string', 'float_n', 'enum', 'enum_float', 'list_',
                   'odict_', 'atom', 'value', 'const'])
    assert members == test


def test_tagged_members2():
    aux = _Aux()
    members = tagged_members(aux, 'pref', [ordered_dict_to_pref,
                                           ordered_dict_from_pref])
    assert list(members) == ['odict_']


def test_tagged_members3():
    aux = _Aux()
    members = sorted(tagged_members(aux).keys())
    test = sorted(['string', 'float_n', 'enum', 'enum_float', 'list_',
                   'odict_', 'atom', 'no_tag', 'value', 'const'])
    assert members == test


def test_member_from_pref1():
    aux = _Aux()
    assert member_from_pref(aux, aux.get_member(str('string')), 'a') == 'a'


def test_member_from_pref2():
    aux = _Aux()
    assert member_from_pref(aux, aux.get_member(
        str('float_n')), '1.0') == 1.0


def test_member_from_pref3():
    aux = _Aux()
    assert member_from_pref(aux, aux.get_member(str('enum')), 'a') == 'a'


def test_member_from_pref4():
    aux = _Aux()
    assert member_from_pref(aux, aux.get_member(
        str('enum_float')), '1.0') == 1.0


def test_member_from_pref5():
    aux = _Aux()
    member = aux.get_member(str('list_'))
    assert member_from_pref(aux, member, '[1.0, 2.0]') == [1.0, 2.0]


def test_member_from_pref6():
    aux = _Aux()
    member = aux.get_member(str('odict_'))
    assert member_from_pref(aux, member, repr([(u'a', 1.0)])) == {"a": 1.0}


def test_member_from_pref7():
    aux = _Aux()
    member = aux.get_member(str('value'))
    assert member_from_pref(aux, member, 'test.test') == 'test.test'


def test_member_to_pref1():
    aux = _Aux()
    assert member_to_pref(aux, aux.get_member(str('string')), 'a') == 'a'


def test_member_to_pref2():
    aux = _Aux()
    assert member_to_pref(aux, aux.get_member(str('float_n')), 1.0) == '1.0'


def test_member_to_pref3():
    aux = _Aux(enum=str('a'))
    assert member_to_pref(aux, aux.get_member(str('enum')), 'a') == 'a'


def test_member_to_pref4():
    aux = _Aux()
    assert member_to_pref(aux, aux.get_member(
        str('enum_float')), 1.0) == '1.0'


def test_member_to_pref5():
    aux = _Aux()
    member = aux.get_member(str('list_'))
    assert member_to_pref(aux, member, [1.0, 2.0]) == '[1.0, 2.0]'


def test_member_to_pref6():
    aux = _Aux()
    member = aux.get_member(str('odict_'))
    assert member_to_pref(aux, member, {"a": 1.0}) == repr([(u'a', 1.0)])


def test_member_to_pref7():
    aux = _Aux()
    member = aux.get_member(str('value'))
    assert member_to_pref(aux, member, 'test.test') == 'test.test'


def test_update_members_from_pref():
    aux = _Aux()
    pref = {'float_n': '1.0',
            'enum': 'a',
            'enum_float': '1.0',
            'list_': "[2.0, 5.0]",
            'odict_': "{'a': 1.0}",
            'atom': {'int_': '2'},
            'const': 'r'}
    aux.update_members_from_preferences(pref)
    assert aux.float_n == 1.0
    assert aux.enum == 'a'
    assert aux.enum_float == 1.0
    assert aux.list_ == [2.0, 5.0]
    assert aux.odict_ == {'a': 1.0}
    assert aux.atom.int_ == 2

    aux.atom = None
    pref = {'atom': {'int_': '2'}}
    aux.update_members_from_preferences(pref)
    assert aux.atom is None

    pref = {'enum': 'c'}
    with pytest.raises(ValueError):
        aux.update_members_from_preferences(pref)


def test_pref_from_members():
    aux = _Aux()
    pref = aux.preferences_from_members()
    assert pref['string'] == ''
    assert pref['float_n'] == '0.0'
    assert pref['enum'] == 'a'
    assert pref['enum_float'] == '1.0'
    assert pref['list_'] == '[]'
    assert pref['odict_'] == '[]'
    assert pref['atom'] == {'int_': '0'}
