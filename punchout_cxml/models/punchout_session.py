# Copyright 2023 ACSONE SA/NV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from base64 import b64decode
from io import StringIO

import lxml.etree as ET
import requests
from lxml.etree import XMLSyntaxError

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PunchoutSession(models.Model):
    _inherit = "punchout.session"

    def _render_cxml_operation(self, template_xml_id, template_values=None):
        """Render a cXML operation using a QWeb template."""
        self.ensure_one()
        backend = self.backend_id
        template_values = template_values or {}
        template_values.update(
            {"session": self, "backend": backend, "user": self.env.user}
        )
        cxml = (
            self.env["ir.ui.view"]
            .sudo()
            ._render_template(template_xml_id, values=template_values)
        )
        cxml_request_element = ET.fromstring(cxml)
        ET.indent(cxml_request_element)
        cxml_request_str = ET.tostring(
            cxml_request_element,
            encoding="UTF-8",
            xml_declaration=True,
            pretty_print=True,
            doctype=backend._get_cxml_dtd_declaration(),
        ).decode("utf-8")
        return cxml_request_str

    def _get_punchout_request_setup(self, session):
        """Generate cXML PunchOutSetupRequest."""
        user_email = self._get_punchout_request_user_email()
        if not user_email:
            raise UserError(
                _(
                    "You must set a personal email in your preferences "
                    "in order to access this feature."
                )
            )
        cxml_request_str = session._render_cxml_operation(
            "punchout_cxml.cxml_punchout_PunchOutSetupRequest"
        )
        return cxml_request_str

    @api.model
    def _check_punchout_request_ok(self, response):
        """Validate cXML response status."""
        res = True
        response_tree = ET.fromstring(response.content)
        cxml_status_code = 0
        cxml_status_text = ""
        for cxml_status in response_tree.findall("./Response/Status"):
            cxml_status_code = int(cxml_status.attrib.get("code", 0))
            cxml_status_text = cxml_status.attrib.get("text", "")
        if not response.ok:
            log_msg = (
                f"PunchOut {self._name}: {response.status_code}: "
                f"{response.reason}\n"
                f"URL: {response.url}"
            )
            _logger.error(log_msg)
            raise UserError(log_msg)
        if not 200 <= cxml_status_code <= 400:
            log_msg = (
                f"PunchOut {self._name}: cXML {cxml_status_code}: "
                f"{cxml_status_text}\n"
                f"URL: {response.url}"
            )
            _logger.error(log_msg)
            raise UserError(
                _(
                    "The PunchOut request with URL %(url)s returned "
                    "%(status_code)s (%(reason)s)."
                )
                % {
                    "url": response.url,
                    "status_code": cxml_status_code,
                    "reason": cxml_status_text,
                }
            )
        return res

    def _get_post_punchout_setup_url(self, session):
        """Post cXML PunchOutSetupRequest and get start URL."""
        if session.backend_id.protocol != "cxml":
            return super()._get_post_punchout_setup_url(session)

        punchout_backend = session.backend_id
        punchout_setup_url = punchout_backend.url
        cxml_request_str = self._get_punchout_request_setup(session)
        _logger.info("PunchOut %s: posting cXML setup request", self._name)
        response = requests.post(
            punchout_setup_url,
            data=cxml_request_str,
            headers={"Content-Type": "text/xml"},
            timeout=30,
        )
        response_tree = ET.fromstring(response.content)
        session.write(
            {
                "setup_request": cxml_request_str,
                "setup_request_response": ET.tostring(response_tree, pretty_print=True),
            }
        )
        if not self._check_punchout_request_ok(response):
            return {}

        start_page_url = ""
        for url in response_tree.findall(
            "./Response/PunchOutSetupResponse/StartPage/URL"
        ):
            start_page_url = url.text
        return start_page_url

    @api.model
    def _store_punchout_session_response(self, backend_id, response_data):
        """Store cXML response and find matching session by BuyerCookie."""
        backend = self.env["punchout.backend"].sudo().browse(backend_id)
        if backend.protocol != "cxml":
            return super()._store_punchout_session_response(backend_id, response_data)

        cxml_string = response_data
        if isinstance(cxml_string, bytes):
            cxml_string = cxml_string.decode()

        cxml = cxml_string.encode()
        tree = ET.fromstring(cxml)
        buyer_cookie_elem = tree.find(".//BuyerCookie")
        buyer_cookie_id = (
            buyer_cookie_elem.text.strip() if buyer_cookie_elem is not None else ""
        )
        if not buyer_cookie_id:
            _logger.error(
                "Unable to find a buyer cookie from the cXML punchout response \n%s",
                ET.tostring(tree, pretty_print=True),
            )
            return False

        session = self.sudo().search(
            [
                ("buyer_cookie_id", "=", buyer_cookie_id),
                ("backend_id", "=", backend_id),
            ],
            limit=1,
        )
        if not session:
            _logger.error(
                "[punchout.cxml.match] backend=%s cookie=%s no session found",
                backend_id,
                buyer_cookie_id,
            )
            return False
        # Lock the row so a concurrent callback (replay, retry) for
        # the same session can't race us into double-processing.
        self.env.cr.execute(
            "SELECT id FROM punchout_session WHERE id = %s FOR UPDATE",
            (session.id,),
        )

        session.write(
            {
                "response": ET.tostring(tree, pretty_print=True),
                "response_date": fields.Datetime.now(),
            }
        )
        xml_validation = session._validate_response()
        is_valid = xml_validation.get("valid")
        if is_valid:
            session.write({"state": "to_process"})
        else:
            session.write(
                {"state": "error", "error_message": xml_validation.get("error")}
            )
        if session.expiration_date <= fields.Datetime.now():
            session.write(
                {"state": "error", "error_message": "punchout.session expired"}
            )
        return session

    def _validate_response(self):
        """Validate cXML response against DTD if configured."""
        self.ensure_one()
        if self.backend_id.protocol != "cxml":
            return super()._validate_response()

        cxml = self.response
        if not cxml:
            return {"valid": True}

        tree = ET.fromstring(cxml)
        backend = self.backend_id
        dtd_data = backend.dtd_file
        if not dtd_data:
            return {"valid": True}
        try:
            dtd_file = b64decode(dtd_data).decode()
            dtd_io = StringIO(dtd_file)
            dtd = ET.DTD(dtd_io)
            dtd.validate(tree)
            dtd_io.close()
        except XMLSyntaxError as e:
            _logger.exception(e)
            return {
                "valid": False,
                "error": e.msg,
            }
        return {
            "valid": True,
        }
