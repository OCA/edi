# Copyright 2023 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
import textwrap

import mock

from odoo.addons.component.tests.common import SavepointComponentCase
from odoo.addons.edi_oca.tests.common import EDIBackendTestMixin


class TestProcessComponent(SavepointComponentCase, EDIBackendTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend = cls._get_backend()
        cls.exc_type = cls._create_exchange_type(
            name="Test Product import",
            code="test_product_import",
            direction="input",
            exchange_file_ext="xml",
            exchange_filename_pattern="{record.identifier}-{type.code}-{dt}",
            backend_id=cls.backend.id,
            advanced_settings_edit=textwrap.dedent(
                """
            components:
                process:
                    usage: input.process.product
            product_import:
                wiz_ctx:
                    random_key: custom
            """
            ),
        )
        cls.record = cls.backend.create_record("test_product_import", {})
        cls.record._set_file_content(b"<fake><product></product></fake>")
        cls.wiz_model = cls.env["product.import"]

    def test_lookup(self):
        comp = self.backend._get_component(self.record, "process")
        self.assertEqual(comp._name, "edi.input.product.process")

    def test_wizard_setup(self):
        comp = self.backend._get_component(self.record, "process")
        with mock.patch.object(
            type(self.wiz_model), "product_file_change"
        ) as md_onchange:
            wiz = comp._setup_wizard()
            self.assertEqual(wiz._name, self.wiz_model._name)
            self.assertEqual(wiz.env.context["random_key"], "custom")
            self.assertEqual(
                base64.b64decode(wiz.product_file), b"<fake><product></product></fake>"
            )
            self.assertEqual(wiz.product_filename, self.record.exchange_filename)
            md_onchange.assert_called()

    def test_import_product(self):
        comp = self.backend._get_component(self.record, "process")
        mock1 = mock.patch.object(type(self.wiz_model), "product_file_change")
        mock2 = mock.patch.object(type(self.wiz_model), "import_button")
        # Simulate the wizard
        with mock1 as md_onchange, mock2 as md_btn:
            res = comp.process()
            md_onchange.assert_called()
            md_btn.assert_called()
        self.assertEqual(res, "Products created")
