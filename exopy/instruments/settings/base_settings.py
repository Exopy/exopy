# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2015-2018 by Exopy Authors, see AUTHORS for more details.
#
# Distributed under the terms of the BSD license.
#
# The full license is in the file LICENCE, distributed with this software.
# -----------------------------------------------------------------------------
"""Base classes to handle driver settings edition.

Settings are architecture specific information. Then can allow to select a
if several are available for example.

"""
from atom.api import Unicode, ForwardTyped, Bool
from enaml.core.api import d_, Declarative, d_func
from enaml.widgets.api import GroupBox


class BaseSettings(GroupBox):
    """Base widget for creating settings.

    """
    #: Id of this settings (different from the declaration one as multiple
    #: settings of the same type can exist for a single instrument).
    user_id = d_(Unicode())

    #: Reference to the declaration that created this object.
    declaration = d_(ForwardTyped(lambda: Settings))

    #: Whether or not to make the settings editable
    read_only = d_(Bool())

    @d_func
    def gather_infos(self):
        """Return the current values as a dictionary.

        The base funcion should always be called (using
        BaseSettings.gather_infos as super is not allowed in declarative
        functions) and all values should be strings.

        """
        return {'id': self.declaration.id, 'user_id': self.user_id}

    def _default_title(self):
        return self.user_id + ' (' + self.declaration.id + ')'

    def _post_setattr_user_id(self, old, new):
        if self.declaration:
            self.title = new + ' (' + self.declaration.id + ')'


class Settings(Declarative):
    """A declarative class for contributing a driver settings.

    Settings object can be contributed as extensions child to the
    'settings' extension point of the 'exopy.instruments' plugin.

    """
    #: Unique name used to identify the editor.
    id = d_(Unicode())

    #: Connection description.
    description = d_(Unicode())

    @d_func
    def new(self, workbench, defaults, read_only):
        """Create a new setting and instantiate it properly.

        Defaults should be used to update the created setting.

        """
        raise NotImplementedError()
