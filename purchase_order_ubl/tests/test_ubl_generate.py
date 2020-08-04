# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import HttpCase


class TestUblOrder(HttpCase):

    def test_ubl_generate(self):
        ro = self.env.ref('purchase.report_purchase_quotation')
        poo = self.env['purchase.order']
        buo = self.env['base.ubl']
        order_states = poo.get_order_states()
        rfq_states = poo.get_rfq_states()
        for i in range(7):
            i += 1
            order = self.env.ref('purchase.purchase_order_%d' % i)
            for version in ['2.0', '2.1']:
                pdf_file = ro.with_context(
                    ubl_version=version,
                    force_report_rendering=True
                ).render_qweb_pdf(order.ids)[0]
                res = buo.get_xml_files_from_pdf(pdf_file)
                if order.state in order_states:
                    filename = order.get_ubl_filename(
                        'order', version=version)
                    self.assertTrue(filename in res)
                elif order.state in rfq_states:
                    filename = order.get_ubl_filename('rfq', version=version)
                    self.assertTrue(filename in res)
