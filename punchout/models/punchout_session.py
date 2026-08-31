# Copyright 2023 ACSONE SA/NV
# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import os
import random
import time
from datetime import datetime
from urllib.parse import urlparse
from uuid import uuid4

import pytz
from dateutil.relativedelta import relativedelta

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

    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=True,
        help=(
            "Human-readable label used wherever a punchout session is "
            "referenced in the UI (Many2one displays, smart button "
            "captions, log messages). Built from the backend name and "
            "creation date so a stale 'punchout.session,42' never "
            "leaks into purchaser-facing screens."
        ),
    )
    backend_id = fields.Many2one(
        comodel_name="punchout.backend",
        readonly=True,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        readonly=True,
        default=lambda self: self.env.uid,
    )
    buyer_cookie_id = fields.Char(readonly=True, string="Cookie")
    punchout_url = fields.Char(readonly=True, string="Start URL")
    setup_request = fields.Text(
        readonly=True,
    )
    setup_request_response = fields.Text(
        readonly=True,
    )
    response = fields.Text(
        readonly=True,
    )
    response_date = fields.Datetime(
        readonly=True,
    )
    expiration_date = fields.Datetime(
        compute="_compute_expiration_date",
        store=True,
        readonly=True,
        compute_sudo=True,
    )
    error_message = fields.Text(
        readonly=True,
    )
    state = fields.Selection(
        selection="_selection_state",
        default="draft",
        tracking=True,
        readonly=True,
    )
    action_process_allowed = fields.Boolean(compute="_compute_action_process_allowed")

    @api.depends(
        "state",
    )
    def _compute_action_process_allowed(self):
        for rec in self:
            rec.action_process_allowed = rec.state in ("to_process", "error")

    @api.depends("backend_id.name", "create_date")
    def _compute_name(self):
        for rec in self:
            backend_name = rec.backend_id.name or _("(no backend)")
            if rec.create_date:
                stamp = rec.create_date.strftime("%Y-%m-%d %H:%M")
                rec.name = f"{backend_name} / {stamp}"
            else:
                rec.name = backend_name

    @api.depends(
        "backend_id",
        "create_date",
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
        pid = f"{os.getpid():03d}"
        random_numbers_list = [random.randint(0, 9) for _ in range(5)]
        random_numbers = "".join(map(str, random_numbers_list))
        return f"{timestamp}{pid}{random_numbers}@{domain}"

    def _get_punchout_buyer_cookie(self):
        return f"{self.env.user.id}-{uuid4()}"

    def _get_punchout_request_user_email(self):
        return self.env.user.email

    def _get_post_punchout_setup_url(self, session):
        """Post setup request and get start URL. Override in protocol modules."""
        raise NotImplementedError(
            _("Protocol %(protocol)s does not implement setup request.")
            % {"protocol": session.backend_id.protocol}
        )

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
    def _store_punchout_session_response(self, backend_id, response_data):
        """Store response and find matching session. Override in protocol modules."""
        raise NotImplementedError(_("Protocol does not implement response storage."))

    def _validate_response(self):
        """Validate the response. Override in protocol modules."""
        return {"valid": True}

    def _check_action_process_allowed(self):
        for rec in self:
            if not rec.action_process_allowed:
                raise UserError(
                    _("You are not allowed to process this request. " "%(name)s")
                    % {"name": rec.display_name}
                )

    def action_process(self):
        self.ensure_one()
        self._check_action_process_allowed()
        self.sudo().write({"state": "done", "error_message": False})
        return True

    def _get_redirect_url(self):
        """Where to send the user's browser after the supplier POSTs the
        cart back. Default: the session form so the user sees the parsed
        cart and can decide what to do next. Override in subclasses to
        skip straight to a generated PO."""
        self.ensure_one()
        if self.state in ("to_process", "error"):
            return f"/web#id={self.id}&model=punchout.session&view_type=form"
        return "/web"

    @api.model
    def _gc_punchout_sessions(self):
        """Delete sessions older than each backend's
        ``session_retention_days``. Backends with retention=0 keep
        their sessions forever (not recommended).

        Triggered by the scheduled action shipped in
        ``data/ir_cron.xml``; no-ops if no backend has a positive
        retention configured."""
        backends = self.env["punchout.backend"].search(
            [("session_retention_days", ">", 0)]
        )
        deleted_total = 0
        for backend in backends:
            cutoff = fields.Datetime.now() - relativedelta(
                days=backend.session_retention_days
            )
            stale = self.search(
                [
                    ("backend_id", "=", backend.id),
                    ("create_date", "<", cutoff),
                ]
            )
            if stale:
                count = len(stale)
                stale.unlink()
                deleted_total += count
                _logger.info(
                    "[punchout.gc] backend=%s deleted=%d cutoff=%s",
                    backend.name,
                    count,
                    cutoff,
                )
        return deleted_total
