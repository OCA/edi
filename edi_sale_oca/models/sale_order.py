# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahaw@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = [
        "sale.order",
        "edi.exchange.consumer.mixin",
    ]
    # Receiver may send or not the response on create
    # then for each update IF required.
    # https://docs.oasis-open.org/ubl/os-UBL-2.3/UBL-2.3.html#S-ORDERING-POST-AWARD
    # https://docs.peppol.eu/poacc/upgrade-3/profiles/28-ordering
    # /#_response_code_on_header_level

    # TBD: implementing OrdResp for all modifications
    # can be complex to manage (also for the 3rd party).
    # Hence, we could block further modifications w/ sale exceptions
    # and ask the sender to issue a new order request.
    # This approach seems suitable only for orders that do not get processed immediately.

    disable_edi_auto = fields.Boolean(
        states={"draft": [("readonly", False)]},
    )

    # edi_record_metadata api
    def _edi_get_metadata_to_store(self, orig_vals):
        data = super()._edi_get_metadata_to_store(orig_vals)
        # collect line values
        line_vals_by_edi_id = {}
        for line_vals in orig_vals.get("order_line", []):
            # line_vals in the form `(0, 0, vals)`
            vals = line_vals[-1]
            line_vals_by_edi_id[vals["edi_id"]] = vals

        data.update({"orig_values": {"lines": line_vals_by_edi_id}})
        return data


class SaleOrderLine(models.Model):
    _name = "sale.order.line"
    _inherit = [
        "sale.order.line",
        "edi.exchange.consumer.mixin",
        "edi.id.mixin",
    ]

    disable_edi_auto = fields.Boolean(related="order_id.disable_edi_auto")

    # TODO: add test
    edi_exchange_ready = fields.Boolean(compute="_compute_edi_exchange_ready")

    @api.depends()
    def _compute_edi_exchange_ready(self):
        for rec in self:
            rec.edi_exchange_ready = rec._edi_exchange_ready()

    def _edi_exchange_ready(self):
        # TODO: not sure we want to exclude lines w/o qty.
        # We could have lines that are replaced and kept w/ no qty.
        # ATM we don't give full info on replacements on such lines.
        # Lines are simply marked as changed.
        return (
            not self._is_delivery()
            and not self.display_type
            and bool(self.product_uom_qty)
        )
