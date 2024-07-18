# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class EDIConfigPurchaseListener(Component):
    _name = "edi.config.consumer.listener.purchase.order"
    _inherit = "base.event.listener"
    _apply_on = ["purchase.order"]

    def on_button_confirm_purchase_order(self, record):
        trigger = "on_button_confirm_purchase_order"
        for rec in record:
            confs = self.env["edi.configuration"].edi_get_conf(trigger, rec._name, rec.partner_id)
            for conf in confs:
                conf.edi_exec_snippet_do(rec)

    def on_record_write(self, record, fields=None, **kwargs):
        trigger = "on_record_write"
        if kwargs.get("vals", False):
            for rec in record:
                confs = self.env["edi.configuration"].edi_get_conf(trigger, rec._name, rec.partner_id)
                for conf in confs:
                    conf.edi_exec_snippet_do(rec, **kwargs)

    def on_record_create(self, record, fields=None, **kwargs):
        trigger = "on_record_create"
        val_list = kwargs.get("vals", False)
        if val_list:
            for rec, vals in zip(record, val_list):
                kwargs["vals"] = {rec.id: vals}
                confs = self.env["edi.configuration"].edi_get_conf(trigger, rec._name, rec.partner_id)
                for conf in confs:
                    conf.edi_exec_snippet_do(rec, **kwargs)
