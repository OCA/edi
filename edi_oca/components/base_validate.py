# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.component.core import AbstractComponent


class EDIBackendValidateComponentMixin(AbstractComponent):
    """Validate exchange data."""

    _name = "edi.component.validate.mixin"
    _inherit = "edi.component.mixin"
    _usage = "edi.validate.*"

    def validate(self, value=None):
        self._validate(value)

    def _validate(self, value=None):
        """Return None validated, raise `edi.exceptions.EDIValidationError` if not."""
        raise NotImplementedError()
