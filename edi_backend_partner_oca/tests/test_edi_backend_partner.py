# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo.addons.edi.tests.common import EDIBackendCommonTestCase

_logger = logging.getLogger(__name__)


class EDIBackendPartnerTestCase(EDIBackendCommonTestCase):
    def test_backend_partner_link(self):
        partner = self.env["res.partner"].create({"name": "TEST EDI partner"})
        self.assertEqual(partner.edi_backend_count, 0)
        self.backend.partner_id = partner
        partner.invalidate_cache()
        self.assertEqual(partner.edi_backend_count, 1)
        # Dummy test for action:
        res = partner.action_edi_backend()
        self.assertTrue(res)
