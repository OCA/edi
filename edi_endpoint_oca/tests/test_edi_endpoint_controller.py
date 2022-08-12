# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import os
import unittest

from odoo.tests.common import HttpCase


@unittest.skipIf(os.getenv("SKIP_HTTP_CASE"), "EDIEndpointHttpCase skipped")
class EDIEndpointHttpCase(HttpCase):
    def setUp(self):
        super().setUp()
        # I don't know why but  when test_edi_endpoint runs before these tests
        # the rollback of the exception catched within the test `test_archive_check`
        # make the controller lookup fail.
        # Since the whole routing registry machinery is going to be refactored
        # in https://github.com/OCA/edi/pull/633
        # let's survive w/ this forced registration for now.
        self.env.ref("edi_endpoint_oca.edi_endpoint_demo_1")._register_controllers(
            init=True
        )

    def test_call1(self):
        response = self.url_open("/edi/demo/try")
        self.assertEqual(response.status_code, 401)
        # Let's login now
        self.authenticate("admin", "admin")
        response = self.url_open("/edi/demo/try")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Created record:", response.content.decode())
