# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .common import BaseTestCase


class ApplicationReceiptTestCase(BaseTestCase):
    def _get_handler(self, usage="gs1.in.ApplicationReceiptAcknowledgement", **kw):
        return self.backend._get_component(work_ctx=dict(), usage=usage, **kw)

    def test_parse(self):
        fname = "ApplicationReceiptAcknowledgement.example1.xml"
        file_content = self.read_test_file(fname)
        handler = self._get_handler()
        result = handler.parse_xml(file_content)
        # expected = {}
        # TODO: improve it
        self.assertTrue(result["applicationReceiptAcknowledgement"])
        self.assertFalse(handler.is_ok(result))
