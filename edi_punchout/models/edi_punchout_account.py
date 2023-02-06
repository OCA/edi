# Copyright 2023 Hunki Enterprises BV (https://hunki-enterprises.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, datetime, timedelta
from urllib.parse import parse_qs, urlparse, urlunparse

from lxml import objectify

from odoo import _, api, exceptions, fields, models
from odoo.osv.expression import FALSE_LEAF


class EdiPunchoutAccount(models.Model):
    _name = "edi.punchout.account"
    _description = "Account for a webshop supporting punchout"
    _rec_name = "partner_id"

    partner_id = fields.Many2one("res.partner", string="Supplier", required=True)
    partner_name = fields.Char(related="partner_id.name", string="Partner name")
    partner_img = fields.Image(related="partner_id.image_128")
    protocol = fields.Selection([("oci", "OCI"), ("ids", "IDS")], default="ids")
    oci_version = fields.Selection(
        [("3.0", "3.0"), ("5.0", "5.0")], default="3.0", string="OCI version",
    )
    ids_version = fields.Selection(
        [("1.3", "1.3"), ("2.5", "2.5")], default="1.3", string="IDS version",
    )
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    group_ids = fields.Many2many(
        "res.groups",
        help="If set, only members of the selected groups can access this account",
    )
    catalog_url = fields.Char(required=True)
    oci_custom_url_parameters = fields.Char(
        "Vendor-specific parameters",
        groups="purchase.group_purchase_manager",
        help="The vendor should have given you authentication parameters in the form"
        "username=user&password=pass",
    )
    oci_custom_url_parameters_html = fields.Char(
        compute="_compute_oci_custom_url_parameters_html", compute_sudo=True
    )
    hook_url = fields.Char(compute="_compute_hook_url")
    product_category_id = fields.Many2one(
        "product.category",
        help="When creating new products, create them in the following category "
        "instead of the default",
    )
    ids_name_kunde = fields.Char("Name", help="Parameter 'name_kunde'")
    ids_kndnr = fields.Char("Number", help="Parameter 'kndnr'")
    ids_pw_kunde = fields.Char("Password", help="Parameter 'pw_kunde'")

    def _compute_hook_url(self):
        base_url = urlparse(
            self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        )
        for this in self:
            this.hook_url = urlunparse(base_url._replace(path="/edi_punchout/return"))

    def _compute_oci_custom_url_parameters_html(self):
        for this in self:
            this.oci_custom_url_parameters_html = "".join(
                '<input type="hidden" name="%s" value="%s" />' % (key, "".join(value))
                for key, value in parse_qs(this.oci_custom_url_parameters).items()
            )

    @api.constrains("oci_custom_url_parameters")
    def _check_oci_custom_url_parameters(self):
        for this in self:
            if not this.oci_custom_url_parameters:
                continue
            try:
                parse_qs(this.oci_custom_url_parameters, strict_parsing=True)
            except ValueError:
                raise exceptions.ValidationError(
                    _(
                        "%s does not seem to be a query string. Note values need to be "
                        "urlencoded, like name=value%20with%20space",
                    )
                    % this.custom_url_parameters,
                )

    def _company(self):
        """Return self's company if it exists or the currently active company"""
        return self.company_id or self.env.company

    def _handle_return(self, data, order=None):
        """
        Create a draft purchase order from the products we got passed from the webshop
        """
        self.ensure_one()
        vals = getattr(self, "_%s_prepare_purchase_order" % self.protocol)(data)
        if order:
            self._update_order(order, vals)
            return order
        return self.env["purchase.order"].create(vals)

    def _update_order(self, order, vals):
        """
        Update existing order after confirming order
        """
        order.write(
            {
                "date_planned": vals.get("date_planned") or order.date_planned,
                "partner_ref": vals.get("partner_ref") or order.partner_ref,
                "order_line": [(6, 0, [])]
                + [order_line_vals for order_line_vals in vals["order_line"]],
            }
        )
        # write state after deleting lines, as we can't delete lines in state purchase
        order.write({"state": "purchase" if order.state == "ids_send" else order.state})

    def _ids_prepare_purchase_order(self, shopping_cart):
        """
        Return the values to create a purchase order based on shopping_cart
        This is a string containing XML as specified by IDS
        """
        self.ensure_one()
        order = objectify.fromstring(shopping_cart.encode("utf8"))
        return {
            "company_id": self._company().id,
            "partner_id": self.partner_id.id,
            "partner_ref": getattr(
                order.Order.OrderInfo,
                "OrderConfNo",
                getattr(order.Order.OrderInfo, "OfferNo", False),
            ),
            "date_planned": str(getattr(order.Order.OrderInfo, "DeliveryDate", ""))[:10]
            or (
                fields.Date.to_string(
                    datetime.strptime(
                        "%s/%.2s/5"
                        % (
                            order.Order.OrderInfo.DeliveryYear,
                            order.Order.OrderInfo.DeliveryWeek,
                        ),
                        "%Y/%W/%w",
                    ).date()
                )
                if getattr(order.Order.OrderInfo, "DeliveryWeek", False)
                and getattr(order.Order.OrderInfo, "DeliveryYear", False)
                else False
            )
            or False,
            "currency_id": (
                self.env["res.currency"].search(
                    [("name", "=", order.Order.OrderInfo.Cur.text)]
                )
                or self._company().currency_id
            ).id,
            "order_line": [
                (0, 0, self._ids_prepare_purchase_order_line(product, order_item))
                for order_item, product in (
                    (order_item, self._ids_get_or_create_product(order_item))
                    for order_item in order.Order.OrderItem
                )
            ],
        }

    def _ids_prepare_purchase_order_line(self, product, order_item):
        """
        Return the values to create a purchase order line
        """
        uom = self._ids_get_or_create_uom(order_item)
        return {
            "product_id": product.id,
            "name": product.name,
            "product_qty": float(order_item.Qty) * uom.factor,
            "price_unit": float(order_item.NetPrice)
            / float(order_item.Qty)
            * uom.factor_inv,
            "date_planned": date.today(),
            "taxes_id": [(6, 0, product.supplier_taxes_id.ids)],
            "product_uom": uom.id,
            "currency_id": (
                self.env["res.currency"].search(
                    [("name", "=", order_item.getparent().OrderInfo.Cur.text)]
                )
                or self._company().currency_id
            ).id,
        }

    def _ids_parse_order_item(self, order_item):
        """
        Translate an IDS item node to a vals dict for creating a product
        """
        self.ensure_one()
        uom = self._ids_get_or_create_uom(order_item)
        reference_uom = self.env["uom.uom"].search(
            [("category_id", "=", uom.category_id.id), ("uom_type", "=", "reference")]
        )
        return {
            "name": order_item.Kurztext.text,
            "type": "product"
            if "product"
            in (
                _tuple[0]
                for _tuple in self.env["product.product"]
                ._fields["type"]
                .selection(self)
            )
            else "consu",
            "purchase_ok": True,
            "barcode": getattr(order_item, "EAN", False),
            "description_purchase": str(getattr(order_item, "Langtext", "")),
            "taxes_id": [
                (
                    6,
                    0,
                    (
                        self.env["account.tax"].search(
                            [
                                ("type_tax_use", "=", "sale"),
                                ("amount", "=", float(order_item.VAT)),
                                ("price_include", "=", False),
                                ("company_id", "=", self._company().id),
                            ],
                            limit=1,
                        )
                        or self._company().account_sale_tax_id
                    ).ids,
                )
            ],
            "uom_id": reference_uom.id,
            "uom_po_id": uom.id,
            "supplier_taxes_id": [
                (
                    6,
                    0,
                    (
                        self.env["account.tax"].search(
                            [
                                ("type_tax_use", "=", "purchase"),
                                ("amount", "=", float(order_item.VAT)),
                                ("price_include", "=", False),
                                ("company_id", "=", self._company().id),
                            ],
                            limit=1,
                        )
                        or self._company().account_purchase_tax_id
                    ).ids,
                )
            ],
            "categ_id": self.product_category_id.id
            or self.env["product.template"]._get_default_category_id(),
            "seller_ids": [
                (
                    0,
                    0,
                    {
                        "name": self.partner_id.id,
                        "product_name": order_item.Kurztext.text,
                        "product_code": order_item.ArtNo.text,
                        "price": float(order_item.NetPrice)
                        / float(order_item.Qty)
                        * uom.factor_inv,
                        "min_qty": 0,
                        "currency_id": (
                            self.env["res.currency"].search(
                                [
                                    (
                                        "name",
                                        "=",
                                        order_item.getparent().OrderInfo.Cur.text,
                                    )
                                ]
                            )
                            or self._company().currency_id
                        ).id,
                    },
                )
            ],
        }

    def _ids_get_or_create_uom(self, order_item):
        """
        Return an existing UOM, or create one based on PriceBasis
        """
        uom = (
            self.env["uom.uom"].search(
                [("ids_name", "=", order_item.QU), ("uom_type", "=", "reference")]
            )
            or self.env["uom.uom"].search(
                [
                    "|",
                    "|",
                    "|",
                    ("ids_name_alternative", "=", order_item.QU),
                    ("ids_name_alternative", "=like", "%% %s" % order_item.QU),
                    ("ids_name_alternative", "=like", "%s %%" % order_item.QU),
                    ("ids_name_alternative", "=like", "%% %s %%" % order_item.QU),
                    ("uom_type", "=", "reference"),
                ]
            )
            or self.env.ref("uom.product_uom_unit")
        )
        price_amount = float(getattr(order_item, "PriceBasis", "1"))
        if price_amount != 1:
            uom = self.env["uom.uom"].search(
                [
                    ("category_id", "=", uom.category_id.id),
                    ("factor", "=", 1 / price_amount),
                ]
            ) or self.env["uom.uom"].sudo().create(
                {
                    "name": "%d %s" % (price_amount, uom.name),
                    "category_id": uom.category_id.id,
                    "factor": 1 / price_amount,
                    "uom_type": "bigger" if price_amount > 1 else "smaller",
                    "ids_name": uom.ids_name,
                }
            )
        return uom

    def _ids_get_or_create_product(self, order_item):
        """
        Return an existing product or a new one matching order_item
        """
        self.ensure_one()
        Product = self.env["product.product"]
        product = Product.search(
            [
                "|",
                "&",
                ("seller_ids.name", "=", self.partner_id.id),
                ("seller_ids.product_code", "=", order_item.ArtNo.text),
                ("barcode", "=", str(order_item.EAN))
                if getattr(order_item, "EAN", False)
                else FALSE_LEAF,
            ],
            limit=1,
        ) or Product.sudo().create(self._ids_parse_order_item(order_item))
        self._ids_update_product(product, order_item)
        if product.company_id and self._company() != product.company_id:
            product.company_id = False
        return product

    def _ids_update_product(self, product, order_item):
        """
        If there is a matching supplier, update price, otherwise add supplier
        """
        product_vals = self._ids_parse_order_item(order_item)
        seller_vals = product_vals["seller_ids"][0][2]
        matching_seller = None
        factor = 1
        if product.uom_po_id.id != product_vals["uom_po_id"]:
            factor = (
                product.uom_po_id.factor_inv
                / self.env["uom.uom"].browse(product_vals["uom_po_id"]).factor_inv
            )
        seller_vals["price"] *= factor
        for seller in product.seller_ids:
            if (
                seller.name == self.partner_id
                and seller.product_code == seller_vals["product_code"]
                and seller.currency_id.id == seller_vals["currency_id"]
                and seller.min_qty == seller_vals["min_qty"]
            ):
                matching_seller = seller
                break
        if matching_seller:
            matching_seller.sudo().price = seller_vals["price"]
        else:
            product.sudo().write({"seller_ids": [(0, 0, seller_vals)]})

    def _oci_prepare_purchase_order(self, product_dicts):
        """
        Return the values to create a purchase order based on product_dicts
        Those are dicts with the 'NEW_ITEM-' prefix removed from the keys
        """
        self.ensure_one()
        return {
            "company_id": self._company().id,
            "partner_id": self.partner_id.id,
            "order_line": [
                (0, 0, self._oci_prepare_purchase_order_line(product, product_dict))
                for product_dict, product in (
                    (product_dict, self._oci_get_or_create_product(product_dict))
                    for product_dict in product_dicts
                )
            ],
        }

    def _oci_prepare_purchase_order_line(self, product, product_dict):
        """
        Return the values to create a purchase order line
        """
        return {
            "product_id": product.id,
            "name": product.name,
            "product_qty": float(product_dict["QUANTITY"]),
            "price_unit": float(product_dict["PRICE"]),
            "date_planned": date.today()
            + timedelta(days=float(product_dict.get("LEADTIME", 0))),
            "taxes_id": [(6, 0, product.supplier_taxes_id.ids)],
            # TODO use UOM from product_dict
            "product_uom": product.uom_id.id,
        }

    def _oci_parse_product_dict(self, product_dict):
        """
        Translate a dict as passed via OCI to a vals dict for creating a product
        """
        self.ensure_one()
        return {
            "name": product_dict["DESCRIPTION"],
            "type": "consu",
            "purchase_ok": True,
            "description_purchase": product_dict.get("LONGTEXT")
            if product_dict.get("LONGTEXT") != product_dict["DESCRIPTION"]
            else None,
            "seller_ids": [
                (
                    0,
                    0,
                    {
                        "name": self.partner_id.id,
                        "product_name": product_dict["DESCRIPTION"],
                        "product_code": product_dict["VENDORMAT"],
                        "delay": product_dict.get("LEADTIME", 0),
                        "price": float(product_dict["PRICE"]),
                        # TODO handle UNIT, PRICEUNIT, CURRENCY
                    },
                )
            ],
        }

    def _oci_get_or_create_product(self, product_dict):
        """
        Return an existing product or a new one matching product_dict
        """
        self.ensure_one()
        Product = self.env["product.product"]
        product = Product.search(
            [
                ("seller_ids.name", "=", self.partner_id.id),
                ("seller_ids.product_code", "=", product_dict["VENDORMAT"]),
            ],
            limit=1,
        ) or Product.sudo().create(self._oci_parse_product_dict(product_dict))
        if product.company_id and self._company() != product.company_id:
            product.company_id = False
        return product
