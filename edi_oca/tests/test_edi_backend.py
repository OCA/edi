# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import psycopg2

from odoo.tools import mute_logger

from .common import EDIBackendCommonTestCase


class EDIBackendTestCase(EDIBackendCommonTestCase):
    def test_type_code(self):
        btype = self.backend_type_model.create(
            {"name": "Test new type", "code": "Test new type"}
        )
        self.assertEqual(btype.code, "test_new_type")

    @mute_logger("odoo.sql_db")
    def test_type_code_uniq(self):
        existing_code = self.backend.backend_type_id.code
        with self.assertRaises(psycopg2.IntegrityError):
            self.backend_type_model.create(
                {"name": "Test new type", "code": existing_code}
            )
