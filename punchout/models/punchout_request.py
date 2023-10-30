# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import os
import random
import time
from datetime import datetime
from urllib.parse import urlparse
from uuid import uuid4

import lxml.etree as ET
import pytz
import requests
from cryptography.fernet import Fernet, InvalidToken

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PunchoutRequest(models.Model):
    _name = "punchout.request"
    _inherit = [
        "mail.thread",
    ]
    _order = "create_date desc"
    _description = "Punchout Request"

    backend_id = fields.Many2one(comodel_name="punchout.backend", readonly=True,)
    user_id = fields.Many2one(
        comodel_name="res.users", readonly=True, default=lambda self: self.env.uid,
    )
    buyer_cookie_id = fields.Char(readonly=True, string="Cookie")
    punchout_url = fields.Char(readonly=True, string="Start URL")
    cxml_response = fields.Text(readonly=True, string="Response",)
    cxml_response_date = fields.Datetime(readonly=True, string="Response Date",)
    error_message = fields.Text(readonly=True,)
    state = fields.Selection(
        selection="_selection_state", default="draft", tracking=True,
    )
    action_process_allowed = fields.Boolean(compute="_compute_action_process_allowed")

    @api.depends("state",)
    def _compute_action_process_allowed(self):
        for rec in self:
            rec.action_process_allowed = rec.state in ("to_process", "error")

    @api.model
    def _selection_state(self):
        return [
            ("draft", _("Draft")),
            ("error", _("Error")),
            ("to_process", _("To Process")),
            ("done", _("Done")),
        ]

    @api.model
    def _get_punchout_request_timestamp(self):
        """
        Get ISO 8601 timestamp
        """
        current_time = datetime.now()
        timezone = pytz.timezone(self.env.user.tz)
        localized_time = current_time.astimezone(timezone)
        return localized_time.strftime("%Y-%m-%dT%H:%M:%S%z")

    def _get_punchout_payload_identity(self):
        ir_config_parameter_model = self.env["ir.config_parameter"].sudo()
        base_url = ir_config_parameter_model.get_param("web.base.url")
        parsed_url = urlparse(base_url)
        domain = parsed_url.netloc
        timestamp = int(time.time())
        pid = "{:03d}".format(os.getpid())
        random_numbers_list = [random.randint(0, 9) for _ in range(5)]
        random_numbers = "".join(map(str, random_numbers_list))
        return f"{timestamp}{pid}{random_numbers}@{domain}"

    @api.model
    def _get_punchout_request_header_credential(self, backend, header, credential_type):
        """
        Adds the asked credential tag in the header.
        :param backend: punchout.backend
        :param header: xml.etree.ElementTree.Element (header)
        :param credential_type: "From", "To" or "Sender"
        :return: xml.etree.ElementTree.Element (header)
        """
        header_cred_type = ET.SubElement(header, credential_type)
        cred_domain, cred_identity = backend._get_domain_and_identity(credential_type)
        header_cred = ET.SubElement(
            header_cred_type, "Credential", attrib={"domain": cred_domain}
        )
        ET.SubElement(header_cred, "Identity").text = cred_identity
        if credential_type == "Sender":
            ET.SubElement(header_cred, "SharedSecret").text = backend.shared_secret
            ET.SubElement(header_cred_type, "UserAgent").text = backend.user_agent
        return header

    def _get_punchout_request_header(self, cxml, backend):
        """
        Adds the header tag in the cXML PunchOut request element.
        :param cxml: xml.etree.ElementTree.Element (cxml)
        :param backend: punchout.backend
        :return: xml.etree.ElementTree.Element (cxml)
        """
        header = ET.SubElement(cxml, "Header")
        self._get_punchout_request_header_credential(backend, header, "From")
        self._get_punchout_request_header_credential(backend, header, "To")
        self._get_punchout_request_header_credential(backend, header, "Sender")
        return cxml

    def _get_punchout_buyer_cookie(self):
        return f"{self.env.user.id}-{uuid4()}"

    def _get_encrypted_punchout_buyer_cookie(self, backend, buyer_cookie):
        encyrption_key = backend.buyer_cookie_encryption_key.encode()
        return Fernet(encyrption_key).encrypt(buyer_cookie.encode("utf-8"))

    def _get_punchout_request_user_email(self):
        return self.env.user.email

    def _get_punchout_request_setup(self, backend, buyer_cookie_id):
        payload_id = self._get_punchout_payload_identity()
        request_timestamp = self._get_punchout_request_timestamp()
        encrypted_buyer_cookie_id = self._get_encrypted_punchout_buyer_cookie(
            backend, buyer_cookie_id
        )
        user_email = self._get_punchout_request_user_email()
        if not user_email:
            raise UserError(
                _(
                    "You must set a personnal email in your preferences "
                    "in order to access this feature."
                )
            )
        cxml = ET.Element(
            "cXML",
            attrib={
                "version": "1.2.008",
                "{http://www.w3.org/XML/1998/namespace}lang": "en",
                "payloadID": payload_id,
                "timestamp": request_timestamp,
            },
        )
        self._get_punchout_request_header(cxml, backend)

        deployment_mode = backend.deployment_mode
        request = ET.SubElement(
            cxml, "Request", attrib={"deploymentMode": deployment_mode}
        )
        setup_request = ET.SubElement(
            request, "PunchOutSetupRequest", attrib={"operation": "create"}
        )
        ET.SubElement(setup_request, "BuyerCookie").text = encrypted_buyer_cookie_id
        ET.SubElement(
            setup_request, "Extrinsic", attrib={"name": "UserEmail"}
        ).text = user_email
        browser_form_post = ET.SubElement(setup_request, "BrowserFormPost")
        ET.SubElement(
            browser_form_post, "URL"
        ).text = backend._get_browser_form_post_url()
        return cxml

    @api.model
    def _check_punchout_request_ok(self, response):
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
            self.env.user.notify_warning(
                title=_("PunchOut request error"),
                message=_(
                    f"The PunchOut request with URL {response.url} returned "
                    f"{response.status_code} ({response.reason})."
                ),
                sticky=True,
            )
            res = False
        if not 200 <= cxml_status_code <= 400:
            log_msg = (
                f"PunchOut {self._name}: cXML {cxml_status_code}: "
                f"{cxml_status_text}\n"
                f"URL: {response.url}"
            )
            _logger.error(log_msg)
            self.env.user.notify_warning(
                title=_("PunchOut request error"),
                message=_(
                    f"The PunchOut request with URL {response.url} returned "
                    f"cXML {cxml_status_code} ({cxml_status_text})."
                ),
                sticky=True,
            )
            res = False
        return res

    def _get_post_punchout_setup_url(self, punchout_backend, buyer_cookie_id):
        punchout_setup_url = punchout_backend.url
        cxml_request_element = self._get_punchout_request_setup(
            punchout_backend, buyer_cookie_id
        )
        cxml_request_str = ET.tostring(
            cxml_request_element,
            encoding="UTF-8",
            xml_declaration=True,
            pretty_print=True,
            doctype='<!DOCTYPE cXML SYSTEM "http://xml.cxml.org/schemas/cXML/1.2.008/'
            'cXML.dtd">',
        ).decode("utf-8")
        _logger.info("PunchOut %s: posting setup request", self._name)
        response = requests.post(
            punchout_setup_url,
            data=cxml_request_str,
            headers={"Content-Type": "text/xml"},
            timeout=30,
        )
        if not self._check_punchout_request_ok(response):
            return {}
        response_tree = ET.fromstring(response.content)
        start_page_url = ""
        for url in response_tree.findall(
            "./Response/PunchOutSetupResponse/StartPage/URL"
        ):
            start_page_url = url.text
        return start_page_url

    @api.model
    def _redirect_to_punchout(self):
        request = self.sudo()._create_punchout_request()
        return {
            "type": "ir.actions.act_url",
            "url": request.punchout_url,
            "target": "new",
        }

    @api.model
    def _create_punchout_request(self):
        punchout_backend = self._get_punchout_backend_to_use()
        buyer_cookie_id = self._get_punchout_buyer_cookie()
        url = self._get_post_punchout_setup_url(punchout_backend, buyer_cookie_id)
        return self.env["punchout.request"].create(
            {
                "user_id": self.env.user.id,
                "punchout_url": url,
                "buyer_cookie_id": buyer_cookie_id,
                "backend_id": punchout_backend.id,
            }
        )

    @api.model
    def _get_punchout_backend_to_use(self):
        punchout_backend_model = self.env["punchout.backend"]
        punchout_backend_id = self.env.context.get("punchout_backend_id")
        if punchout_backend_id:
            backend = punchout_backend_model.browse(punchout_backend_id)
        else:
            backend = punchout_backend_model.search([], limit=1)
        if not backend:
            raise UserError(
                _("No punchout backend found to initialize the connection.")
            )
        return backend

    @api.model
    def _store_punchout_request(self, backend_id, cxml_string):
        backend = self.env["punchout.backend"].sudo().browse(backend_id)
        tree = ET.fromstring(cxml_string.encode())
        buyer_cookie = tree.find(".//BuyerCookie")
        encrypted_buyer_cookie_id = (
            buyer_cookie.text.strip() if buyer_cookie is not None else False
        )
        if not encrypted_buyer_cookie_id:
            _logger.error(
                "Unable to find a buyer cookie from the cXml punchout response \n%s",
                ET.tostring(tree, pretty_print=True),
            )
            return False
        encryption_key = backend.buyer_cookie_encryption_key.encode()
        fernet = Fernet(encryption_key)
        encrypted_buyer_cookie_id_b = encrypted_buyer_cookie_id.encode()

        try:
            buyer_cookie_id = fernet.decrypt(encrypted_buyer_cookie_id_b).decode()
        except InvalidToken:
            _logger.error(
                "Unable to decode given buyer cookie. %s", encrypted_buyer_cookie_id
            )
            return False

        request = self.sudo().search(
            [("buyer_cookie_id", "=", buyer_cookie_id)], limit=1,
        )
        if not request:
            _logger.error(
                "Unable to find a request with given buyer cookie %s", buyer_cookie_id
            )
            return False
        request.with_user(request.user_id).sudo().write(
            {
                "cxml_response": ET.tostring(tree, pretty_print=True),
                "cxml_response_date": fields.Datetime.now(),
                "state": "to_process",
            }
        )
        request._notify_punchout_response_received()
        return request

    def _notify_punchout_response_received(self):
        self.ensure_one()
        user = self.user_id
        user.with_user(user).notify_info(
            title=_("Processing the request"),
            message=_("The response has been received and will be processed."),
            sticky=False,
        )

    def _check_action_process_allowed(self):
        for rec in self:
            if not rec.action_process_allowed:
                raise UserError(
                    _(
                        f"You are not allowed to process this request. "
                        f"{rec.display_name}"
                    )
                )

    def action_process(self):
        self.ensure_one()
        self._check_action_process_allowed()
        self.sudo().write({"state": "done", "error_message": False})
        return True

    def _get_redirect_url(self):
        self.ensure_one()
        return "/web"
