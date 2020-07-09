# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os

import xmlunittest

from odoo.tests.common import SavepointCase

from odoo.addons.component.tests.common import ComponentMixin


class BaseTestCase(SavepointCase, ComponentMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.setUpComponent()
        cls.backend = cls._get_backend()
        # Logistic Services Provider (LSP)
        cls.lsp_partner = cls.env.ref("base.res_partner_3")
        # Logistic Services Client (LSC)
        cls.lsc_partner = cls.env.ref("base.main_partner")
        cls.backend.lsp_partner_id = cls.lsp_partner

        # set fake GLN codes
        cls.lsp_partner.gln_code = "1".zfill(13)
        cls.lsc_partner.gln_code = "2".zfill(13)

    @classmethod
    def _get_backend(cls):
        return cls.env.ref("base_gs1.default_gs1_backend")


class BaseXMLTestCase(BaseTestCase, xmlunittest.XmlTestMixin):
    """Test XML files."""

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

    # @freeze_time("2018-08-10 17:10:00")
    # def check_filename(self, name_template):
    #     """
    #        Test the filename of the export, the name template can have a date
    #        parameter or a date and time parameter
    #     """
    #     day = fields.Date.today().replace('-', '')
    #     time = fields.Datetime.now().split(' ')[1].replace(':', '')
    #     expected = name_template.format(day, time)
    #     with self.backend.work_on(
    #         self.model._name, timestamp=self.timestamp
    #     ) as work:
    #         writer = work.component(usage='local.xml.writer')
    #         self.assertEqual(writer.filename(), expected)
    #         writer = work.component(usage='sftp.xml.writer')
    #         self.assertEqual(writer.filename(), expected)
