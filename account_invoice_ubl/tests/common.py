# Copyright 2016-2017 Akretion (http://www.akretion.com)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


class TestUblInvoiceMixin:
    def _create_invoice(
        self, product=False, qty=1, price=12.42, discount=0, validate=True
    ):
        aio = self.env["account.move"]
        ato = self.env["account.tax"]
        company = self.env.ref("base.main_company")
        taxes = ato.search(
            [
                ("company_id", "=", company.id),
                ("type_tax_use", "=", "sale"),
                ("unece_type_id", "!=", False),
                ("unece_categ_id", "!=", False),
                ("amount_type", "=", "percent"),
            ]
        )
        if taxes:
            tax = taxes[0]
        else:
            unece_type_id = self.env.ref("account_tax_unece.tax_type_vat").id
            unece_categ_id = self.env.ref("account_tax_unece.tax_categ_s").id
            tax = ato.create(
                {
                    "name": "German VAT purchase 18.0%",
                    "description": "DE-VAT-sale-18.0",
                    "company_id": company.id,
                    "type_tax_use": "sale",
                    "price_include": False,
                    "amount": 18,
                    "amount_type": "percent",
                    "unece_type_id": unece_type_id,
                    "unece_categ_id": unece_categ_id,
                }
            )
        # validate invoice
        if not product:
            product = self.env.ref("product.product_product_4")
        invoice = aio.create(
            {
                "partner_id": self.env.ref("base.res_partner_2").id,
                "currency_id": self.env.ref("base.EUR").id,
                "move_type": "out_invoice",
                "company_id": company.id,
                "name": "SO1242",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_id": product.uom_id.id,
                            "quantity": qty,
                            "price_unit": price,
                            "discount": discount,
                            "name": product.name,
                            "tax_ids": [(6, 0, [tax.id])],
                        },
                    )
                ],
            }
        )
        if validate:
            invoice.action_post()
        return invoice
