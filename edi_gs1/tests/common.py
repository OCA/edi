# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os

import xmlunittest

from odoo.tests.common import tagged

from odoo.addons.component.tests.common import SavepointComponentCase


@tagged("-at_install", "post_install")
class BaseTestCase(SavepointComponentCase, xmlunittest.XmlTestMixin):

    _schema_path = "edi_gs1:static/schemas/sbdh/StandardBusinessDocumentHeader.xsd"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.backend = cls._get_backend()
        # Logistic Services Provider (LSP)
        cls.lsp_partner = cls.env.ref("base.res_partner_3")
        # Logistic Services Client (LSC)
        cls.lsc_partner = cls.env.ref("base.main_partner")
        cls.backend.lsp_partner_id = cls.lsp_partner
        cls.backend.lsc_partner_id = cls.lsc_partner

        # set fake GLN codes
        cls.lsp_partner.gln_code = "1".zfill(13)
        cls.lsc_partner.gln_code = "2".zfill(13)
        # We have to trigger this gs1_code update manually in case of a submodule
        # update them.
        cls.env["uom.uom"]._execute_gs1_map_code()

    @classmethod
    def _get_backend(cls):
        return cls.env.ref("edi_gs1.edi_backend_gs1_default")

    def _dev_write_example_file(self, test_file, filename, content):
        from pathlib import Path

        path = Path(test_file).parent / ("examples/test." + filename)
        with open(path, "w") as out:
            out.write(content)

    def flatten(self, txt):
        return "".join([x.strip() for x in txt.splitlines()])

    def read_test_file(self, filename):
        path = os.path.join(os.path.dirname(__file__), "examples", filename)
        with open(path, "r") as thefile:
            return thefile.read()

    _schema_path = ""

    def _get_xml_handler(self):
        return self.backend._find_component(
            self.backend._name,
            ["edi.xml"],
            work_ctx={"schema_path": self._schema_path},
            safe=False,
        )
