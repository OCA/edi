# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os

from odoo.tests.common import SavepointCase, tagged


@tagged("-at_install", "post_install")
class EDIBackendCommonTestCase(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context, tracking_disable=True, test_queue_job_no_delay=True
            )
        )
        cls.backend = cls._get_backend()
        cls.backend_model = cls.env["edi.backend"]
        cls.backend_type_model = cls.env["edi.backend.type"]

    def read_test_file(self, filename):
        path = os.path.join(os.path.dirname(__file__), "examples", filename)
        with open(path, "r") as thefile:
            return thefile.read()

    @classmethod
    def _get_backend(cls):
        return cls.env.ref("edi.demo_edi_backend")
