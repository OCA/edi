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
        cls.weak_weap = cls.env.ref("base_wamas.wamas_document_template_weak_weap")
        cls.weakq_weapq = cls.env.ref("base_wamas.wamas_document_template_weakq_weapq")
        cls.tmpfile_path = tempfile.mkstemp(suffix=".txt")[1]

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.tmpfile_path):
            os.remove(cls.tmpfile_path)
        return super().tearDownClass()

    def test_weak_weap(self):
        path = "base_wamas/tests/files/SAMPLE_WEAK_WEAP.txt"
        self._run_full_workflow(path, self.weak_weap)

    def test_weakq_weapq(self):
        path = "base_wamas/tests/files/SAMPLE_WEAKQ_WEAPQ.txt"
        self._run_full_workflow(path, self.weakq_weapq)

    def _run_full_workflow(self, path, template_rec):
        # Get the data from WAMAS document file
        result = []

        with file_open(path) as f:
            for row in f:
                found_element = template_rec.get_proper_element_from_row(row)

                if not found_element:
                    continue

                values = found_element.get_values_from_element(
                    row, convert_type=True, result_type="list_tuple"
                )
                result.append(values)

        # Generate WAMAS document file from the `result` above
        lst_lines = []

        for items in result:
            found_element = template_rec.get_proper_element_from_items(items)
            if not found_element:
                continue

            str_line = found_element.set_values_to_element(items)
            if str_line:
                lst_lines.append(str_line + "\n")

        if lst_lines:
            with open(self.tmpfile_path, "w") as f:
                f.writelines(lst_lines)

        # Compare 2 files
        self.assertTrue(filecmp.cmp(file_path(path), self.tmpfile_path))
