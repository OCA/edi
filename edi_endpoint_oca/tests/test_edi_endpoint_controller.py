# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import os
import unittest

from odoo.tests.common import HttpSavepointCase


@unittest.skipIf(os.getenv("SKIP_HTTP_CASE"), "EDIEndpointHttpCase skipped")
class EDIEndpointHttpCase(HttpSavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # force sync for demo records
        cls.env["edi.endpoint"].search([])._handle_registry_sync()

    def test_call1(self):
        response = self.url_open("/edi/demo/try")
        self.assertEqual(response.status_code, 401)
        # Let's login now
        self.authenticate("admin", "admin")
        response = self.url_open("/edi/demo/try")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Created record:", response.content.decode())
