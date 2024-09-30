# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import mock

from odoo.tests.common import Form, SavepointCase


class TestCommon(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.wiz_model = cls.env["product.import"]
        cls.company = cls.env["res.company"].create({"name": "Customer ABC"})
        cls.supplier = cls.env["res.partner"].create(
            {"name": "Catalogue Vendor", "company_id": cls.company.id}
        )

    def _mock(self, method_name):
        return mock.patch.object(type(self.wiz_model), method_name)

    @property
    def wiz_form(self):
        return Form(self.wiz_model)
