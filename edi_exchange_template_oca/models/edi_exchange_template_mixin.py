# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import datetime
import logging
import textwrap

import pytz

from odoo import fields, models
from odoo.tools import DotDict, safe_eval

_logger = logging.getLogger(__name__)


def date_to_datetime(dt):
    """Convert date to datetime."""
    if isinstance(dt, datetime.date):
        return datetime.datetime.combine(dt, datetime.datetime.min.time())
    return dt


def to_utc(dt):
    """Convert date or datetime to UTC."""
    # Gracefully convert to datetime if needed 1st
    return date_to_datetime(dt).astimezone(pytz.UTC)


class EDIExchangeTemplateMixin(models.AbstractModel):
    """Define a common ground for EDI exchange templates."""

    _name = "edi.exchange.template.mixin"
    _description = "EDI Exchange Output Mixin"

    name = fields.Char(required=True)
    # TODO: make unique, autocompute slugified name
    code = fields.Char(required=True, index=True)
    backend_type_id = fields.Many2one(
        string="EDI Backend type",
        comodel_name="edi.backend.type",
        ondelete="restrict",
        required=True,
    )
    type_id = fields.Many2one(
        string="EDI Exchange type",
        comodel_name="edi.exchange.type",
        ondelete="cascade",
        auto_join=True,
    )
    backend_id = fields.Many2one(
        comodel_name="edi.backend",
        ondelete="cascade",
        # TODO: default to type_id if given, validate otherwise
    )
    # TODO: add default content w/ comment on what you can use
    code_snippet = fields.Text()
    code_snippet_docs = fields.Text(
        compute="_compute_code_snippet_docs",
        default=lambda self: self._default_code_snippet_docs(),
    )

    def _compute_code_snippet_docs(self):
        for rec in self:
            rec.code_snippet_docs = textwrap.dedent(rec._default_code_snippet_docs())

    def _default_code_snippet_docs(self):
        return """
        Available vars:
        * datetime
        * dateutil
        * time
        * uid
        * user
        * DotDict
        """

    def _code_snippet_valued(self):
        snippet = self.code_snippet or ""
        return bool(
            [
                not line.startswith("#")
                for line in (snippet.splitlines())
                if line.strip("")
            ]
        )

    @staticmethod
    def _utc_now():
        return datetime.datetime.utcnow().isoformat()

    @staticmethod
    def _date_to_string(dt, utc=True):
        if not dt:
            return ""
        if utc:
            dt = to_utc(dt)
        return fields.Date.to_string(dt)

    @staticmethod
    def _datetime_to_string(dt, utc=True):
        if not dt:
            return ""
        if utc:
            dt = to_utc(dt)
        return fields.Datetime.to_string(dt)

    def _get_code_snippet_eval_context(self):
        """Prepare the context used when evaluating python code

        :returns: dict -- evaluation context given to safe_eval
        """
        ctx = {
            "uid": self.env.uid,
            "user": self.env.user,
            "DotDict": DotDict,
        }
        ctx.update(self._time_utils())
        return ctx

    def _time_utils(self):
        return {
            "datetime": safe_eval.datetime,
            "dateutil": safe_eval.dateutil,
            "time": safe_eval.time,
            "utc_now": self._utc_now,
            "date_to_string": self._date_to_string,
            "datetime_to_string": self._datetime_to_string,
            "time_to_string": lambda dt: dt.strftime("%H:%M:%S") if dt else "",
            "first_of": fields.first,
        }

    def _evaluate_code_snippet(self, **render_values):
        if not self._code_snippet_valued():
            return {}
        eval_ctx = dict(render_values, **self._get_code_snippet_eval_context())
        safe_eval.safe_eval(self.code_snippet, eval_ctx, mode="exec", nocopy=True)
        result = eval_ctx.get("result", {})
        if not isinstance(result, dict):
            _logger.error("code_snippet should return a dict into `result`")
            return {}
        return result

    def _get_validator(self, exchange_record):
        # TODO: lookup for validator (
        # can be to validate received file or generated file)
        pass

    def validate(self, exchange_record):
        pass
