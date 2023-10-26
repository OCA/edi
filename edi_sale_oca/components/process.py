# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _
from odoo.exceptions import UserError

from odoo.addons.component.core import Component


class EDIExchangeSOInput(Component):
    """Process sale orders."""

    _name = "edi.input.sale.order.process"
    _inherit = "edi.component.input.mixin"
    _usage = "input.process.sale.order"

    def process(self):
        wiz = self._setup_wizard()
        res = wiz.import_order_button()
        # TODO: log debug
        if wiz.state == "update" and wiz.sale_id:
            order = wiz.sale_id
            msg = self.msg_order_existing_error
            self._handle_existing_order(order, msg)
            raise UserError(msg)
        else:
            order = self._handle_create_order(res["res_id"])
            return self.msg_order_created % order.name
        raise UserError(self.msg_generic_error)

    @property
    def msg_order_existing_error(self):
        return _("Sales order has already been imported before")

    @property
    def msg_order_created(self):
        return _("Sales order %s created")

    @property
    def msg_generic_error(self):
        return _("Something went wrong with the importing wizard.")

    def _setup_wizard(self):
        """Init a `sale.order.import` instance for current record."""
        # Set the right EDI origin on both order and lines
        edi_defaults = {"origin_exchange_record_id": self.exchange_record.id}
        addtional_ctx = dict(
            sale_order_import__default_vals=dict(order=edi_defaults, lines=edi_defaults)
        )
        wiz = (
            self.env["sale.order.import"]
            .with_context(**addtional_ctx)
            .sudo()
            .create({})
        )
        wiz.order_file = self.exchange_record._get_file_content(binary=False)
        wiz.order_filename = self.exchange_record.exchange_filename
        wiz.order_file_change()
        return wiz

    def _handle_create_order(self, order_id):
        order = self.env["sale.order"].browse(order_id)
        self.exchange_record._set_related_record(order)
        return order

    def _handle_existing_order(self, order, message):
        prev_record = self._get_previous_record(order)
        self.exchange_record.message_post_with_view(
            "edi_sale_oca.message_already_imported",
            values={
                "order": order,
                "prev_record": prev_record,
                "message": message,
                "level": "info",
            },
            subtype_id=self.env.ref("mail.mt_note").id,
        )

    def _get_previous_record(self, order):
        return self.env["edi.exchange.record"].search(
            [("model", "=", "sale.order"), ("res_id", "=", order.id)], limit=1
        )
