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
        """Endpoint to import an UBL order.

        Example to test from the terminal:

        curl -X POST -d @tests/examples/test_invoice.xml \
             -H "Content-Type: application/xml" \
             -H "API-KEY: your-secret-key" \
            http://localhost/ubl_api/sales

        """
        return self._import_sale_order()

    def _import_sale_order(
        self,
        method_name="import_ubl_from_http",
        job_values=None,
        final_message=None,
        **kw
    ):
        req = request.httprequest
        env = request.env
        if req.content_type != "application/xml":
            raise werkzeug.exceptions.UnsupportedMediaType()
        self.check_api_key(env, request.auth_api_key_id)
        xml_data = req.get_data()
        self.check_data_to_import(env, xml_data)

        job_values = job_values or {}
        if "description" not in job_values:
            job_values["description"] = "Import UBL order from http"

        model = env["sale.order"].with_delay(**job_values)
        getattr(model, method_name)(xml_data.decode("utf-8"))
        final_message = (
            final_message or "Thank you. Your order will be processed, shortly"
        )
        return final_message

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

    def check_api_key(self, env, api_key_id):
        """Check the api key being used is valid.

        By default this function test that the user linked to the key is the
        one created by the module.
        """
        api_key = env["auth.api.key"].browse(api_key_id)
        if not api_key.exists():
            raise werkzeug.exceptions.Unauthorized()
        if api_key.user_id != env.ref("sale_order_import_ubl_http.user_endpoint"):
            raise werkzeug.exceptions.Unauthorized()
