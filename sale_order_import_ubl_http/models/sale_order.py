# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from base64 import b64encode

from odoo import _, api, models
from odoo.exceptions import UserError

from odoo.addons.queue_job.job import job


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    @job(default_channel="root.ubl_import")
    def import_ubl_from_http(self, data):
        """Job called by the endpoint to import received data."""
        wiz = self.env["sale.order.import"].create({})
        wiz.order_file = b64encode(str.encode(data))
        wiz.order_filename = "imported_invoice.xml"
        wiz.order_file_change()
        wiz.price_source = self._get_default_price_source()
        res = wiz.sudo().import_order_button()
        action_xmlid = res["xml_id"]
        if action_xmlid == "sale_order_import.sale_order_import_action":
            # TODO: Order has already been imported
            #   there could be more than one to update ?
            return _("Sales order has already been imported before, nothing done.")
        elif action_xmlid == "sale.action_quotations":
            order_id = res["res_id"]
            order = self.env["sale.order"].browse(order_id)
            order.action_confirm()
            return _("Sales order {} created").format(order.name)
        else:
            raise UserError(_("Something went wrong with the importing wizard."))

    @api.model
    def _get_default_price_source(self):
        return "pricelist"
