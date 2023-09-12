# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.edi_oca.tests.common import EDIBackendCommonTestCase


class TestEdiWebService(EDIBackendCommonTestCase):
    @classmethod
    def _setup_records(cls):
        result = super()._setup_records()
        cls.webservice = cls.env["webservice.backend"].create(
            {
                "name": "WebService",
                "protocol": "http",
                "url": "http://localhost.demo.odoo/",
                "content_type": "application/xml",
                "tech_name": "demo_ws",
                "auth_type": "none",
            }
        )
        vals = {
            "model": cls.partner._name,
            "res_id": cls.partner.id,
        }
        cls.record = cls.backend.create_record("test_csv_input", vals)
        return result

    def test_components_with_ws(self):
        self.backend.webservice_backend_id = self.webservice
        components = self.backend._get_component_usage_candidates(self.record, "send")
        self.assertIn("webservice.send", components)

    def test_components_without_ws(self):
        components = self.backend._get_component_usage_candidates(self.record, "send")
        self.assertNotIn("webservice.send", components)
