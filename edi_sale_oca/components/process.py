# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, api
from odoo.exceptions import UserError

from odoo.addons.component.core import Component


class EDIExchangeSOInput(Component):
    """Process sale orders."""

    _name = "edi.input.sale.order.process"
    _inherit = "edi.component.input.mixin"
    _usage = "input.process.sale.order"

    def __init__(self, work_context):
        super().__init__(work_context)
        self.settings = {}
        # Suppor legacy key `self.type_settings`
        for key in ("sale_order", "sale_order_import"):
            if key in self.type_settings:
                self.settings = self.type_settings.get(key, {})
                break

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
            order_id = res["res_id"]
            order = self.env["sale.order"].browse(order_id)
            if self._order_should_be_confirmed():
                order.action_confirm()
            self.exchange_record.sudo()._set_related_record(order)
            order._edi_set_origin(self.exchange_record)
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
        ctx = self.settings.get("wiz_ctx", {})
        wiz = self.env["sale.order.import"].with_context(**ctx).sudo().create({})
        wiz.order_file = self.exchange_record._get_file_content(binary=False)
        wiz.order_filename = self.exchange_record.exchange_filename
        wiz.order_file_change()
        wiz.price_source = self._get_default_price_source()
        return wiz

    @api.model
    def _get_default_price_source(self):
        return self.settings.get("price_source", "pricelist")

    def _order_should_be_confirmed(self):
        return self.settings.get("confirm_order", False)

    def _handle_existing_order(self, order, message):
        prev_record = self._get_previous_record(order)
        self.exchange_record.message_post_with_view(
            "edi_sale_order_import.message_already_imported",
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
