# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import os
import random
import time
from base64 import b64decode
from datetime import datetime
from io import StringIO
from urllib.parse import urlparse
from uuid import uuid4

import lxml.etree as ET
import pytz
import requests
from dateutil.relativedelta import relativedelta
from lxml.etree import XMLSyntaxError

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PunchoutSession(models.Model):
    _name = "punchout.session"
    _inherit = [
        "mail.thread",
    ]
    _order = "create_date desc"
    _description = "Punchout Session"

    backend_id = fields.Many2one(comodel_name="punchout.backend", readonly=True,)
    user_id = fields.Many2one(
        comodel_name="res.users", readonly=True, default=lambda self: self.env.uid,
    )
    buyer_cookie_id = fields.Char(readonly=True, string="Cookie")
    punchout_url = fields.Char(readonly=True, string="Start URL")
    cxml_setup_request = fields.Text(readonly=True, string="Setup Request",)
    cxml_setup_request_response = fields.Text(
        readonly=True, string="Setup Request Response",
    )
    cxml_response = fields.Text(readonly=True, string="Response",)
    cxml_response_date = fields.Datetime(readonly=True, string="Response Date",)
    expiration_date = fields.Datetime(
        compute="_compute_expiration_date",
        store=True,
        readonly=True,
        compute_sudo=True,
    )
    error_message = fields.Text(readonly=True,)
    state = fields.Selection(
        selection="_selection_state", default="draft", tracking=True,
    )
    action_process_allowed = fields.Boolean(compute="_compute_action_process_allowed")

    @api.depends("state",)
    def _compute_action_process_allowed(self):
        for rec in self:
            rec.action_process_allowed = rec.state in ("to_process", "error")

    @api.depends(
        "backend_id", "create_date",
    )
    def _compute_expiration_date(self):
        for rec in self:
            ref_date = rec.create_date or fields.Datetime.now()
            rec.expiration_date = ref_date + relativedelta(
                seconds=rec.backend_id.session_duration
            )

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
        timezone = pytz.timezone(self.env.user.tz or "UTC")
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

    def _get_punchout_buyer_cookie(self):
        return f"{self.env.user.id}-{uuid4()}"

    def _get_punchout_request_user_email(self):
        return self.env.user.email

    def _render_cxml_operation(self, template_xml_id, template_values=None):
        self.ensure_one()
        backend = self.backend_id
        template_values = template_values or {}
        template_values.update(
            {"session": self, "backend": backend, "user": self.env.user}
        )
        cxml = (
            self.env["ir.ui.view"]
            .sudo()
            .render_template(template_xml_id, template_values)
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
        user_email = self._get_punchout_request_user_email()
        if not user_email:
            raise UserError(
                _(
                    "You must set a personnal email in your preferences "
                    "in order to access this feature."
                )
            )
        cxml_request_str = session._render_cxml_operation(
            "punchout.cxml_punchout_PunchOutSetupRequest"
        )
        return cxml_request_str

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
                    "The PunchOut request with URL {url} returned "
                    "{status_code} ({reason})."
                ).format(
                    url=response.url,
                    status_code=cxml_status_code,
                    reason=cxml_status_text,
                )
            )
        return res

    def _get_post_punchout_setup_url(self, session):
        punchout_backend = session.backend_id
        punchout_setup_url = punchout_backend.url
        cxml_request_str = self._get_punchout_request_setup(session)
        _logger.info("PunchOut %s: posting setup request", self._name)
        response = requests.post(
            punchout_setup_url,
            data=cxml_request_str,
            headers={"Content-Type": "text/xml"},
            timeout=30,
        )
        response_tree = ET.fromstring(response.content)
        session.write(
            {
                "cxml_setup_request": cxml_request_str,
                "cxml_setup_request_response": ET.tostring(
                    response_tree, pretty_print=True
                ),
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
    def _redirect_to_punchout(self):
        session = self.sudo()._create_punchout_session()
        if not session.punchout_url:
            return False
        return {
            "type": "ir.actions.act_url",
            "url": session.punchout_url,
            "target": "new",
        }

    @api.model
    def _create_punchout_session(self):
        punchout_backend = self._get_punchout_backend_to_use()
        buyer_cookie_id = self._get_punchout_buyer_cookie()
        session = self.env["punchout.session"].create(
            {
                "user_id": self.env.user.id,
                "buyer_cookie_id": buyer_cookie_id,
                "backend_id": punchout_backend.id,
            }
        )
        url = self._get_post_punchout_setup_url(session)
        if url:
            session.write({"punchout_url": url})
        return session

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
    def _store_punchout_session_response(self, backend_id, cxml_string):
        cxml = cxml_string.encode()
        tree = ET.fromstring(cxml)
        buyer_cookie_elem = tree.find(".//BuyerCookie")
        buyer_cookie_id = (
            buyer_cookie_elem.text.strip() if buyer_cookie_elem is not None else ""
        )
        if not buyer_cookie_id:
            _logger.error(
                "Unable to find a buyer cookie from the cXml punchout response \n%s",
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
                "Unable to find a request with given buyer cookie %s", buyer_cookie_id
            )
            return False

        session.write(
            {
                "cxml_response": ET.tostring(tree, pretty_print=True),
                "cxml_response_date": fields.Datetime.now(),
            }
        )
        xml_validation = session._validate_cxml()
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

    def _validate_cxml(self):
        self.ensure_one()
        cxml = self.cxml_response
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
