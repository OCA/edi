# Copyright 2020 ACSONE SA
# Copyright 2020 Creu Blanca
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class EDIBackend(models.Model):
    """Generic backend to control EDI exchanges.

    Backends can be organized with types.
    """

    _name = "edi.backend"
    _description = "EDI Backend"
    _inherit = ["collection.base"]

    name = fields.Char(required=True)
    backend_type_id = fields.Many2one(
        string="EDI Backend type",
        comodel_name="edi.backend.type",
        required=True,
        ondelete="restrict",
    )

    def _get_component(self, safe=False, work_ctx=None, **kw):
        """Retrieve components for current backend.

        :param safe: boolean, if true does not break if component is not found
        :param work_ctx: dictionary with work context params
        :param kw: keyword args to lookup for components (eg: usage)
        """
        work_ctx = work_ctx or {}
        with self.work_on(self._name, **work_ctx) as work:
            if safe:
                component = work.many_components(**kw)
                return component[0] if component else None
            return work.component(**kw)

    def create_record(self, type_code, values):
        """Create an exchange record for current backend.

        :param type_code: edi.exchange.type code
        :param values: edi.exchange.record values
        :return: edi.exchange.record record
        """
        self.ensure_one()
        export_type = self.env["edi.exchange.type"].search(
            [("code", "=", type_code), ("backend_id", "=", self.id)], limit=1
        )
        export_type.ensure_one()
        values["type_id"] = export_type.id
        return self.env["edi.exchange.record"].create(values)
