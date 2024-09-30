# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class EDIBackendListenerComponentConfig(Component):
    _name = "edi.component.listener.config"
    _inherit = "base.event.listener"

    # Added *_configuration to avoid being called from other create/write actions.
    def on_record_write_configuration(self, record, fields=None, **kwargs):
        trigger = "on_record_write"
        if kwargs.get("vals", False):
            for rec in record:
                confs = self.env["edi.configuration"].edi_get_conf(
                    trigger, rec._name, rec.partner_id
                )
                for conf in confs:
                    conf.edi_exec_snippet_do(rec, **kwargs)

    # Added *_configuration to avoid being called from other create/write actions.
    def on_record_create_configuration(self, record, fields=None, **kwargs):
        trigger = "on_record_create"
        val_list = kwargs.get("vals", False)
        if val_list:
            for rec, vals in zip(record, val_list):
                kwargs["vals"] = {rec.id: vals}
                confs = self.env["edi.configuration"].edi_get_conf(
                    trigger, rec._name, rec.partner_id
                )
                for conf in confs:
                    conf.edi_exec_snippet_do(rec, **kwargs)
