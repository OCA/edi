# Copyright 2020 ACSONE SA
# Copyright 2020 Creu Blanca
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import base64
import logging

from odoo import _, exceptions, fields, models, tools

_logger = logging.getLogger(__name__)


class EDIBackend(models.Model):
    """Generic backend to control EDI exchanges.

    Backends can be organized with types.

    The backend should be responsible for generating export records.
    For each record it can generate or parse their values
    depending on their direction (incoming, outgoing).
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

    def exchange_send(self, exchange_record):
        """Send exchange file."""
        self.ensure_one()
        exchange_record.ensure_one()
        # In case already sent: skip sending and check the state
        check = self._exchange_output_check(exchange_record)
        if not check:
            return False
        try:
            self._exchange_send(exchange_record)
        except Exception as err:
            if self.env.context.get("_edi_send_break_on_error"):
                raise
            error = str(err)
            state = "output_error_on_send"
            message = exchange_record._exchange_send_error_msg()
            res = False
        else:
            message = exchange_record._exchange_sent_msg()
            error = None
            state = "output_sent"
            res = True
        finally:
            exchange_record.edi_exchange_state = state
            exchange_record.exchange_error = error
            if message:
                self._exchange_notify_record(exchange_record, message)
        return res

    def _exchange_output_check(self, exchange_record):
        if exchange_record.direction != "output":
            raise exceptions.UserError(
                _("Record ID=%d is not meant to be sent!") % exchange_record.id
            )
        if not exchange_record.exchange_file:
            raise exceptions.UserError(
                _("Record ID=%d has no file to send!") % exchange_record.id
            )
        return exchange_record.edi_exchange_state in [
            "output_pending",
            "output_error_on_send",
        ]

    def _exchange_send(self, exchange_record):
        # TODO: maybe lookup for an `exchange_record.model` specific component 1st
        component = self._get_component(usage="edi.send.%s" % self.backend_type_id.code)
        if component:
            return component.send(exchange_record)
        raise NotImplementedError()

    def _exchange_notify_record(self, record, message, level="info"):
        """Attach notification of exchange state to the original record."""
        if not hasattr(record.record, "message_post_with_view"):
            return
        record.record.message_post_with_view(
            "edi.message_edi_exchange_link",
            values={
                "backend": self,
                "exchange_record": record,
                "message": message,
                "level": level,
            },
            subtype_id=self.env.ref("mail.mt_note").id,
        )
