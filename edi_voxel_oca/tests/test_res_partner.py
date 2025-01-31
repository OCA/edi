# Copyright 2019 Tecnativa - Ernesto Tejeda
# Copyright 2025 Guavana - Leonardo J. Caballero G.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase

class TestResPartner(TransactionCase):

    def setUp(self):
        super(TestResPartner, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'vat': 'ES12345678',
            'voxel_enabled': True,
        })

    def test_commercial_fields(self):
        commercial_fields = self.partner._commercial_fields()
        self.assertIn('voxel_enabled', commercial_fields, "voxel_enabled should be in the commercial fields")

    def test_get_voxel_vat_with_prefix(self):
        vat = self.partner._get_voxel_vat()
        self.assertEqual(vat, '12345678', "VAT should be stripped of the 'ES' prefix")

    def test_get_voxel_vat_without_prefix(self):
        self.partner.vat = '12345678'
        vat = self.partner._get_voxel_vat()
        self.assertEqual(vat, '12345678', "VAT should remain unchanged if no 'ES' prefix")
