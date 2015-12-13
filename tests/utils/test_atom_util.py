# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015 by Ecpy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Test the Atom utility functions and HasPrefAtom object.

"""
from __future__ import (division, unicode_literals, print_function,
                        absolute_import)

from atom.api import (Unicode, Float, Enum, List, Dict, Typed, Int, Value,
                      Constant)
from ecpy.utils.atom_util import (tagged_members, member_from_str, HasPrefAtom)


class _Aaux(HasPrefAtom):

    int_ = Int().tag(pref=True)


class _Aux(HasPrefAtom):

    string = Unicode().tag(pref=True)
    float_n = Float().tag(pref=False)
    enum = Enum('a', 'b').tag(pref=True)
    enum_float = Enum(1.0, 2.0).tag(pref=True)
    list_ = List(Float()).tag(pref=True)
    dict_ = Dict(Unicode(), Float()).tag(pref=True)
    value = Value().tag(pref=True)
    const = Constant('r').tag(pref=True)

    atom = Typed(_Aaux, ()).tag(pref=True)

    no_tag = Int()


def test_tagged_members1():
    aux = _Aux()
    members = sorted(tagged_members(aux, 'pref').keys())
    test = sorted(['string', 'float_n', 'enum', 'enum_float', 'list_',
                   'dict_', 'atom', 'value', 'const'])
    assert members == test


def test_tagged_members2():
    aux = _Aux()
    members = tagged_members(aux, 'pref', False).keys()
    assert members == ['float_n']


def test_tagged_members3():
    aux = _Aux()
    members = sorted(tagged_members(aux).keys())
    test = sorted(['string', 'float_n', 'enum', 'enum_float', 'list_',
                   'dict_', 'atom', 'no_tag', 'value', 'const'])
    assert members == test


def test_member_from_str1():
    aux = _Aux()
    assert member_from_str(aux.get_member(str('string')), 'a') == 'a'


def test_member_from_str2():
    aux = _Aux()
    assert member_from_str(aux.get_member(str('float_n')), '1.0') == 1.0


def test_member_from_str3():
    aux = _Aux()
    assert member_from_str(aux.get_member(str('enum')), 'a') == 'a'


def test_member_from_str4():
    aux = _Aux()
    assert member_from_str(aux.get_member(str('enum_float')), '1.0') == 1.0


def test_member_from_str5():
    aux = _Aux()
    member = aux.get_member(str('list_'))
    assert member_from_str(member, '[1.0, 2.0]') == [1.0, 2.0]


def test_member_from_str6():
    aux = _Aux()
    member = aux.get_member(str('dict_'))
    assert member_from_str(member, '{"a": 1.0}') == {'a': 1.0}


def test_member_from_str7():
    aux = _Aux()
    member = aux.get_member(str('value'))
    assert member_from_str(member, 'test.test') == 'test.test'


def test_update_members_from_pref():
    aux = _Aux()
    pref = {'float_n': '1.0',
            'enum': 'a',
            'enum_float': '1.0',
            'list_': "[2.0, 5.0]",
            'dict_': "{'a': 1.0}",
            'atom': {'int_': '2'},
            'const': 'r'}
    aux.update_members_from_preferences(pref)
    assert aux.float_n == 1.0
    assert aux.enum == 'a'
    assert aux.enum_float == 1.0
    assert aux.list_ == [2.0, 5.0]
    assert aux.dict_ == {'a': 1.0}
    assert aux.atom.int_ == 2

    aux.atom = None
    pref = {'atom': {'int_': '2'}}
    aux.update_members_from_preferences(pref)
    assert aux.atom is None


def test_pref_from_members():
    aux = _Aux()
    pref = aux.preferences_from_members()
    assert pref['string'] == ''
    assert pref['float_n'] == '0.0'
    assert pref['enum'] == 'a'
    assert pref['enum_float'] == '1.0'
    assert pref['list_'] == '[]'
    assert pref['dict_'] == '{}'
    assert pref['atom'] == {'int_': '0'}
