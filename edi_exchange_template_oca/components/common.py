# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.component.core import AbstractComponent


class EDIExchangeInfoMixin(AbstractComponent):
    """Abstract component mixin provide info for exchanges."""

    # TODO: this should be moved to core and renamed to `data`.
    # A `data` component could be used for both incoming and outgoing.

    _name = "edi.info.provider.mixin"
    _inherit = "edi.component.base.mixin"
    # Enable validation of work context attributes
    _work_context_validate_attrs = []

    def __init__(self, work_context):
        super().__init__(work_context)
        for key in self._work_context_validate_attrs:
            if not hasattr(work_context, key):
                raise AttributeError(f"`{key}` is required for this component!")
