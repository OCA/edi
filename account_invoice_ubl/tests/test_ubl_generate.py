# -*- coding: utf-8 -*-
# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# © 2017-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://www.serpentcs.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import TransactionCase
from openerp import workflow


class TestUblInvoice(TransactionCase):

    def test_ubl_generate(self):
        ro = self.registry['report']
        buo = self.env['base.ubl']
        aio = self.env['account.invoice']
        for i in range(2):
            i += 1
            inv_id = ('demo_invoice_%d' % (i+1))
            model_rec = self.env['ir.model.data'].search(
                [('name', '=', inv_id)])
            invoice = aio.browse(model_rec.res_id)
            # validate invoice
            workflow.trg_validate(
                self.uid, 'account.invoice', invoice.id, 'invoice_open',
                self.cr)
            if invoice.type not in ('out_invoice', 'out_refund'):
                continue
            for version in ['2.0', '2.1']:
                # I didn't manage to make it work with new api :-(
                pdf_file = ro.get_pdf(
                    self.cr, self.uid, invoice.ids,
                    'account.report_invoice', context={'ubl_version': version})
                res = buo.get_xml_files_from_pdf(pdf_file)
                invoice_filename = invoice.get_ubl_filename(version=version)
                self.assertTrue(invoice_filename in res)
