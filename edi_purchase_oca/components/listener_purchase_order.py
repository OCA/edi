# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class EDIConfigPurchaseListener(Component):
    _name = "edi.listener.config.purchase.order"
    _inherit = "base.event.listener"
    _apply_on = ["purchase.order"]

    def on_button_confirm_purchase_order(self, record):
        trigger = "on_button_confirm_purchase_order"
        confs = record.mapped("partner_id.edi_purchase_conf_ids").edi_get_conf(trigger)
        for conf in confs:
            conf.edi_exec_snippet_do(record)
