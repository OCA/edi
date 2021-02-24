# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import api, models
from odoo.osv.expression import AND


class SaleOrderImport(models.TransientModel):
    _inherit = "sale.order.import"

    @api.model
    def _search_existing_order_domain(
        self, parsed_order, commercial_partner, state_domain
    ):
        # Overwrite from sale_order_import module
        # Search for existing order on 'customer_order_number' instead of
        # 'client_order_ref'
        return AND(
            [
                state_domain,
                [
                    ("customer_order_number", "=", parsed_order["order_ref"]),
                    ("commercial_partner_id", "=", commercial_partner.id),
                ],
            ]
        )

    def _prepare_order(self, parsed_order, price_source):
        res = super()._prepare_order(parsed_order, price_source)
        res["customer_order_number"] = parsed_order.get("order_ref")
        res["customer_order_free_ref"] = parsed_order.get("customer_reference", "")
        # Removed because will be computed
        res.pop("client_order_ref")
        return res

    def parse_ubl_sale_order(self, xml_root):
        res = super().parse_ubl_sale_order(xml_root)
        ns = xml_root.nsmap
        main_xmlns = ns.pop(None)
        ns["main"] = main_xmlns
        # TODO: Next migration maybe
        # This part could be extracted in a separate function in the base module
        if "RequestForQuotation" in main_xmlns:
            root_name = "main:RequestForQuotation"
        elif "Order" in main_xmlns:
            root_name = "main:Order"
        customer_ref_xpath = xml_root.xpath(
            "/%s/cbc:CustomerReference" % root_name, namespaces=ns
        )
        if customer_ref_xpath:
            ref = customer_ref_xpath[0].text
            res["customer_reference"] = ref
        return res
