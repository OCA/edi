# Copyright 2024 ForgeFlow
# @author: Jordi Masvidal <jordi.masvidal@forgeflow.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests import common


class TestBaseEDI(common.TransactionCase):
    """Simple test for the CI"""

    def test_category_created(self):
        """Test new EDI module category is created"""
        self.assertTrue(self.env.ref("base_edi.module_category_edi").exists())
