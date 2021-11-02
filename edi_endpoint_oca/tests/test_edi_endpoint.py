# Copyright 2021 Camptcamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo.addons.endpoint.tests.common import CommonEndpoint


class TestEndpoint(CommonEndpoint):
    @classmethod
    def _setup_records(cls):
        super()._setup_records()
        cls.endpoint = cls.env.ref("edi_endpoint_oca.edi_endpoint_demo_1")

    def test_endpoint_find(self):
        self.assertEqual(
            self.env["edi.endpoint"]._find_endpoint("/edi/demo/try"), self.endpoint
        )

    def test_exchange_record(self):
        self.endpoint.create_exchange_record()

    def test_route(self):
        rec = self.endpoint.copy(
            {
                "route": "/noprefix",
            }
        )
        self.assertEqual(rec.route, "/edi/noprefix")
