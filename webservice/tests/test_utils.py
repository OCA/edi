# Copyright 2023 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.tests.common import BaseCase

from odoo.addons.webservice.utils import sanitize_url_for_log


class TestUtils(BaseCase):
    def test_url_cleanup(self):
        url = "https://custom.url/?a=1&apikey=secret&password=moresecret"
        self.assertEqual(sanitize_url_for_log(url), "https://custom.url/?a=1")
