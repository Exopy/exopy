# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Objects used to store tasks, interfaces and configs in the manager.

"""
from atom.api import (Atom, Subclass, Dict)

from .environment_variable.base_envvar import BaseEnvVar


class EnvVarInfos(Atom):
    """An object used to store informations about a env_var.
    """
    #: Class representing this env_var.
    cls = Subclass(BaseEnvVar)

    #: Metadata associated with this task such as group, looping capabilities,
    #: etc
    metadata = Dict()
