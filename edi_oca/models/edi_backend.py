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
        _values = self._create_record_prepare_values(type_code, values)
        return self.env["edi.exchange.record"].create(_values)

    def _create_record_prepare_values(self, type_code, values):
        res = values.copy()  # do not pollute original dict
        export_type = self.env["edi.exchange.type"].search(
            self._get_exchange_type_domain(type_code), limit=1
        )
        export_type.ensure_one()
        res["type_id"] = export_type.id
        res["backend_id"] = self.id
        return res
<<<<<<< HEAD
=======

    def _get_exchange_type_domain(self, code):
        return [
            ("code", "=", code),
            "|",
            ("backend_type_id", "=", self.backend_type_id.id),
            ("backend_id", "=", self.id),
        ]

    def generate_output(self, exchange_record, store=True, force=False, **kw):
        """Generate output content for given exchange record.

        :param exchange_record: edi.exchange.record recordset
        :param store: store output on the record itself
        :param force: allow to re-genetate the content
        :param kw: keyword args to be propagated to output generate handler
        """
        self.ensure_one()
        self._validate_generate_output(exchange_record, force=force)
        output = self._generate_output(exchange_record, **kw)
        if output and store:
            if not isinstance(output, bytes):
                output = output.encode()
            exchange_record.update(
                {
                    "exchange_file": base64.b64encode(output),
                    "edi_exchange_state": "output_pending",
                }
            )
        return tools.pycompat.to_text(output)

    def _validate_generate_output(self, exchange_record, force=False):
        exchange_record.ensure_one()
        if (
            exchange_record.edi_exchange_state != "new"
            and exchange_record.exchange_file
            and not force
        ):
            raise exceptions.UserError(
                _(
                    "Exchange record ID=%d is not in draft state "
                    "and has already an output value."
                )
                % exchange_record.id
            )
        if not exchange_record.direction != "outbound":
            raise exceptions.UserError(
                _("Exchange record ID=%d is not file is not meant to b generated")
                % exchange_record.id
            )
        if exchange_record.exchange_file:
            raise exceptions.UserError(
                _("Exchabge record ID=%d already has a file to process!")
                % exchange_record.id
            )

    def _generate_output(self, exchange_record, **kw):
        """To be implemented"""
        raise NotImplementedError()
>>>>>>> 6df23cc... fixup! edi: small fix/imp on models
