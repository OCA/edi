# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime

import pytz

from odoo import _, api, fields, models, exceptions
from odoo.tools import DotDict, safe_eval


def date_to_datetime(dt):
    """Convert date to datetime."""
    if isinstance(dt, datetime.date):
        return datetime.datetime.combine(dt, datetime.datetime.min.time())
    return dt


def to_utc(dt):
    """Convert date or datetime to UTC."""
    # Gracefully convert to datetime if needed 1st
    return date_to_datetime(dt).astimezone(pytz.UTC)


class EdiConfiguration(models.Model):
    _name = "edi.configuration"

    name = fields.Char(string="Name", required=True)
    active = fields.Boolean(default=True)
    code = fields.Char(required=True, copy=False, index=True, unique=True)
    description = fields.Char(help="Describe what the conf is for")
    backend_id = fields.Many2one(string="Backend", comodel_name="edi.backend")
    type_id = fields.Many2one(
        string="Exchange Type",
        comodel_name="edi.exchange.type",
        ondelete="cascade",
        auto_join=True,
        index=True,
    )
    model = fields.Many2one(
        "ir.model", string="Model", help="Model the conf applies to. Leave blank to apply for all models"
    )
    # TODO: Create the `model_name` field : easy search through the name of the model,
    # eg: in case, we don't know the ID of model,...
    partner_ids = fields.Many2many(
        string="Enabled for partners",
        comodel_name="res.partner",
        relation="res_partner_edi_configuration_rel",
        column1="conf_id",
        column2="partner_id",
        help="Leave blank to apply for all partners."
    )
    trigger = fields.Selection(
        [
            ("on_record_write", "Update Record"),
            ("on_record_create", "Create Record"),
            ("on_email_send", "Send Email"),
        ],
        string="Trigger",
        default=False,
    )
    snippet_before_do = fields.Text(
        string="Snippet Before Do",
        help="Snippet to validate the state and collect records to do",
    )
    snippet_do = fields.Text(
        string="Snippet Do",
        help="""Used to do something specific here.
        Receives: operation, edi_action, vals, old_vals.""",
    )

    @api.constrains("backend_id", "type_id")
    def _constrain_backend(self):
        for rec in self:
            if rec.type_id.backend_id:
                if rec.type_id.backend_id != rec.backend_id:
                    raise exceptions.ValidationError(
                        _("Backend must match with exchange type's backend!")
                    )
            else:
                if rec.type_id.backend_type_id != rec.backend_id.backend_type_id:
                    raise exceptions.ValidationError(
                        _("Backend type must match with exchange type's backend type!")
                    )

    def _code_snippet_valued(self, snippet):
        snippet = snippet or ""
        return bool(
            [
                not line.startswith("#")
                for line in (snippet.splitlines())
                if line.strip("")
            ]
        )

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

    def _time_utils(self):
        return {
            "datetime": safe_eval.datetime,
            "dateutil": safe_eval.dateutil,
            "time": safe_eval.time,
            "utc_now": fields.Datetime.now(),
            "date_to_string": self._date_to_string,
            "datetime_to_string": self._datetime_to_string,
            "time_to_string": lambda dt: dt.strftime("%H:%M:%S") if dt else "",
            "first_of": fields.first,
        }

    def _get_code_snippet_eval_context(self):
        """Prepare the context used when evaluating python code

        :returns: dict -- evaluation context given to safe_eval
        """
        ctx = {
            "uid": self.env.uid,
            "user": self.env.user,
            "DotDict": DotDict,
            "conf": self,
        }
        ctx.update(self._time_utils())
        return ctx

    def _evaluate_code_snippet(self, snippet, **render_values):
        if not self._code_snippet_valued(snippet):
            return {}
        eval_ctx = dict(render_values, **self._get_code_snippet_eval_context())
        safe_eval.safe_eval(snippet, eval_ctx, mode="exec", nocopy=True)
        result = eval_ctx.get("result", {})
        if not isinstance(result, dict):
            return {}
        return result

    def edi_exec_snippet_before_do(self, record, **kwargs):
        self.ensure_one()
        vals = {
            "todo": kwargs.get("todo", True),
        }
        # Execute snippet before do
        vals_before_do = self._evaluate_code_snippet(
            self.snippet_before_do, record=record
        )

        # Prepare data
        vals.update(
            {
                "todo": vals_before_do.get("todo", True),
                "snippet_do_vars": vals_before_do.get("snippet_do_vars", False),
                "event_only": vals_before_do.get("event_only", False),
                "tracked_fields": vals_before_do.get("tracked_fields", False),
                "edi_action": vals_before_do.get("edi_action", False),
            }
        )
        return vals

    def edi_exec_snippet_do(self, record, **kwargs):
        self.ensure_one()

        old_value = kwargs.get("old_vals", {}).get(record.id, {})
        new_value = kwargs.get("vals", {}).get(record.id, {})
        vals = {
            "todo": kwargs.get("todo", True),
            "record": record,
            "operation": kwargs.get("operation", False),
            "edi_action": kwargs.get("edi_action", False),
            "old_value": old_value,
            "vals": new_value,
        }
        if self.snippet_before_do:
            before_do_vals = self.edi_exec_snippet_before_do(record, **kwargs)
            vals.update(before_do_vals)
        if vals["todo"]:
            return self._evaluate_code_snippet(self.snippet_do, **vals)
        return True

    @api.model
    def edi_get_conf(self, trigger, model_name=None, partners=None, backend=None):
        domain = [("trigger", "=", trigger)]
        if model_name:
            domain += [
                "|",
                ("model.model", "=", model_name),
                ("model.model", "=", False)
            ]
        if partners:
            domain += [
                "|",
                ("partner_ids", "in", partners.ids),
                ("partner_ids", "=", False)
            ]
        else:
            domain.append(("partner_ids", "=", False))
        if backend:
            domain.append(("backend_id", "=", backend.id))
        return self.search(domain)
