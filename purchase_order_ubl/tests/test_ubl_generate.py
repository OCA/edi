# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests.common import HttpCase


class TestUblOrder(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ro = cls.env["ir.actions.report"]
        cls.ro = cls.env["ir.actions.report"]
        cls.poo = cls.env["purchase.order"]
        cls.buo = cls.env["base.ubl"]
        cls.order_states = cls.poo.get_order_states()
        cls.rfq_states = cls.poo.get_rfq_states()

    def _test_ubl_generation(self, purchase_order):
        for version in ["2.0", "2.1"]:
            pdf_file = self.ro.with_context(
                ubl_version=version, force_report_rendering=True
            )._render_qweb_pdf(
                "purchase.report_purchase_quotation", purchase_order.ids
            )[
                0
            ]
            res = self.buo.get_xml_files_from_pdf(pdf_file)
            if purchase_order.state in self.order_states:
                filename = purchase_order.get_ubl_filename("order", version=version)
                self.assertTrue(filename in res)
            elif purchase_order.state in self.rfq_states:
                filename = purchase_order.get_ubl_filename("rfq", version=version)
                self.assertTrue(filename in res)

    def test_ubl_generate(self):
        for i in range(1, 8):
            order = self.env.ref("purchase.purchase_order_%d" % i)
            self._test_ubl_generation(order)

    def test_no_error_with_section_and_note_lines(self):
        po = self.env.ref("purchase.purchase_order_1").copy()
        po.write(
            {
                "order_line": [
                    Command.create(
                        {
                            "display_type": "line_section",
                            "name": "Test Section Header",
                            "product_qty": 0.0,
                            "price_unit": 0.0,
                        }
                    ),
                    Command.create(
                        {
                            "display_type": "line_note",
                            "name": "Test Note Content",
                            "product_qty": 0.0,
                            "price_unit": 0.0,
                        }
                    ),
                ]
            }
        )
        self._test_ubl_generation(po)
