# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import filecmp
import os
import tempfile

from odoo.tests.common import TransactionCase
from odoo.tools import file_open, file_path


class TestBaseWamas(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.xml_to_weakweap = cls.env.ref(
            "base_wamas_ubl.wamas_document_xml_conversion_template_from_xml_to_weak_weap"
        )
        cls.weakqweapq_to_xml = cls.env.ref(
            "base_wamas_ubl.wamas_document_xml_conversion_template_from_weakq_weapq_to_xml"
        )
        cls.tmpfile_path_txt = tempfile.mkstemp(suffix=".txt")[1]
        cls.tmpfile_path_xml = tempfile.mkstemp(suffix=".xml")[1]

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.tmpfile_path_txt):
            os.remove(cls.tmpfile_path_txt)
        if os.path.exists(cls.tmpfile_path_xml):
            os.remove(cls.tmpfile_path_xml)
        return super().tearDownClass()

    def test_convert_from_xml_to_weak_weap(self):
        path = "base_wamas_ubl/tests/files/XML2WAMAS-SAMPLE_DESPATCH_ADVICE.xml"
        path_wamas_doc = "base_wamas_ubl/tests/files/XML2WAMAS-SAMPLE_WEAK_WEAP.txt"
        xml_file = file_open(path, "rb").read()

        res = self.xml_to_weakweap.convert_from_xml_to_wamas_document(xml_file)

        if res:
            with open(self.tmpfile_path_txt, "w") as f:
                f.writelines(res)

        # Compare 2 files
        self.assertTrue(filecmp.cmp(file_path(path_wamas_doc), self.tmpfile_path_txt))

    def test_convert_from_weakq_weapq_to_xml(self):
        path = "base_wamas_ubl/tests/files/WAMAS2XML-SAMPLE_WEAKQ_WEAPQ.txt"
        path_xml_doc = "base_wamas_ubl/tests/files/WAMAS2XML-SAMPLE_DESPATCH_ADVICE.xml"

        with file_open(path) as f:
            res = self.weakqweapq_to_xml.convert_from_wamas_document_to_xml(f)

            if res:
                with open(self.tmpfile_path_xml, "wb") as f2:
                    f2.write(res)

        # Compare 2 files
        self.assertTrue(filecmp.cmp(file_path(path_xml_doc), self.tmpfile_path_xml))
