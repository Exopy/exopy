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
from atom.api import Str, Float, Enum, List, Dict, Typed, Int
from ecpy.utils.atom_util import (tagged_members, simple_member_from_str,
                                      member_from_str, HasPrefAtom)

from ..util import complete_line


def setup_module():
    print complete_line(__name__ + ': setup_module()', '~', 78)


def teardown_module():
    print complete_line(__name__ + ': teardown_module()', '~', 78)


class _Aaux(HasPrefAtom):

    int_ = Int().tag(pref=True)


class _Aux(HasPrefAtom):

    string = Str().tag(pref=True)
    float_n = Float().tag(pref=False)
    enum = Enum('a', 'b').tag(pref=True)
    enum_float = Enum(1.0, 2.0).tag(pref=True)
    list_ = List(Float()).tag(pref=True)
    dict_ = Dict(Str(), Float()).tag(pref=True)

    atom = Typed(_Aaux, ()).tag(pref=True)


def test_tagged_members1():
    aux = _Aux()
    members = sorted(tagged_members(aux, 'pref').keys())
    test = sorted(['string', 'float_n', 'enum', 'enum_float', 'list_',
                   'dict_', 'atom'])
    assert members == test


def test_tagged_members2():
    aux = _Aux()
    members = tagged_members(aux, 'pref', False).keys()
    assert members == ['float_n']


def test_simple_member_from_str1():
    aux = _Aux()
    assert simple_member_from_str(aux.get_member('string'), 'a') == 'a'


def test_simple_member_from_str2():
    aux = _Aux()
    assert simple_member_from_str(aux.get_member('float_n'), '1.0') == 1.0


def test_simple_member_from_str3():
    aux = _Aux()
    assert simple_member_from_str(aux.get_member('enum'), 'a') == 'a'


def test_simple_member_from_str4():
    aux = _Aux()
    assert simple_member_from_str(aux.get_member('enum_float'), '1.0') == 1.0


def test_member_from_str1():
    aux = _Aux()
    assert member_from_str(aux.get_member('string'), 'a') == 'a'


def test_member_from_str2():
    aux = _Aux()
    assert member_from_str(aux.get_member('float_n'), '1.0') == 1.0


def test_member_from_str3():
    aux = _Aux()
    assert member_from_str(aux.get_member('enum'), 'a') == 'a'


def test_member_from_str4():
    aux = _Aux()
    assert member_from_str(aux.get_member('enum_float'), '1.0') == 1.0


def test_member_from_str5():
    aux = _Aux()
    member = aux.get_member('list_')
    assert member_from_str(member, '[1.0, 2.0]') == [1.0, 2.0]


def test_member_from_str6():
    aux = _Aux()
    member = aux.get_member('dict_')
    assert member_from_str(member, '{"a": 1.0}') == {'a': 1.0}


def test_update_members_from_pref():
    aux = _Aux()
    pref = {'string': 'a',
            'float_n': '1.0',
            'enum': 'a',
            'enum_float': '1.0',
            'list_': "[2.0, 5.0]",
            'dict_': "{'a': 1.0}",
            'atom': {'int_': '2'}}
    aux.update_members_from_preferences(**pref)
    assert aux.string == 'a'
    assert aux.float_n == 1.0
    assert aux.enum == 'a'
    assert aux.enum_float == 1.0
    assert aux.list_ == [2.0, 5.0]
    assert aux.dict_ == {'a': 1.0}
    assert aux.atom.int_ == 2


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
