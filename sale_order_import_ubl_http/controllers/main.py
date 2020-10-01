# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import werkzeug
from lxml import etree

from odoo import http
from odoo.exceptions import UserError
from odoo.http import request


class ImportController(http.Controller):
    @http.route(
        "/ubl_api/sales", type="http", auth="api_key", methods=["POST"], csrf=False
    )
    def import_sale_order(self, **kw):
        """Endpoint to import an UBL sale order.

        Example to test from the terminal:

        curl -X POST -d @tests/examples/test_invoice.xml \
             -H "Content-Type: application/xml" \
             -H "API-KEY: your-secret-key" \
            http://localhost/ubl_api/sales

        """
        req = request.httprequest
        if req.content_type != "application/xml":
            raise werkzeug.exceptions.UnsupportedMediaType()
        if not self.is_api_key_valid():
            raise werkzeug.exceptions.Unauthorized()
        env = request.env
        xml_data = req.get_data()
        self.check_data_to_import(env, xml_data)
        description = "Import UBL sale order from http"
        xml_data = xml_data.decode("utf-8")
        env["sale.order"].with_delay(description=description).import_ubl_from_http(
            xml_data
        )
        return "Thank you. Your sale order will be processed, shortly"

    def check_data_to_import(self, env, data):
        """ Check the data received looks valid.

        For any problem with the data an exception is raised and the HTTP
        request will return an error.
        """
        try:
            xml_root = etree.fromstring(data)
        except etree.XMLSyntaxError:
            raise werkzeug.exceptions.BadRequest(description="Invalid XML data")
        try:
            env["sale.order.import"].parse_xml_order(xml_root, detect_doc_type=True)
        except UserError:
            raise werkzeug.exceptions.BadRequest(description="Unsupported XML document")

    def is_api_key_valid(self):
        """Check the api key being used is valid.

        By default this function test that the user linked to the key is the
        one created by the module.
        """
        env = request.env
        api_key = env["auth.api.key"].browse(request.auth_api_key_id)
        if api_key.user_id != env.ref("sale_order_import_ubl_http.user_endpoint"):
            return False
        return True
