# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import datetime

import pytz

from odoo import fields
from odoo.tools import DotDict

from odoo.addons.component.core import AbstractComponent


class EDIExchangeInfoMixin(AbstractComponent):
    """Abstract component mixin provide info for exchanges."""

    # TODO: this should be moved to core and renamed to `data`.
    # A `data` component could be used for both incoming and outgoing.

    _name = "edi.info.provider.mixin"
    _inherit = "edi.component.mixin"

    _work_context_validate_attrs = []

    def __init__(self, work_context):
        super().__init__(work_context)
        for key in self._work_context_validate_attrs:
            if not hasattr(work_context, key):
                raise AttributeError(f"`{key}` is required for this component!")

    # TODO: rename this to something generic, like `compute_info`
    # or `load_info` whatever
    def generate_info(self):
        """Generate and return data for output info.

        :return: odoo.tools.DotDict
        """
        return DotDict(self._generate_info())

    def _generate_info(self):
        raise NotImplementedError("You must provide `_generate_info`")

    @property
    def replace_existing(self):
        """Pass `replace_existing` to work context to change this value."""
        return getattr(self.work, "replace_existing", False)

    # helper methods
    @staticmethod
    def _utc_now():
        return datetime.datetime.utcnow().isoformat()

    @staticmethod
    def date_to_string(dt, utc=True):
        if utc:
            dt = dt.astimezone(pytz.UTC)
        return fields.Date.to_string(dt)
