# Copyright 2020 ACSONE SA
# Copyright 2020 Creu Blanca
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from lxml import etree

from odoo import api, fields, models
from odoo.tools import safe_eval

from odoo.addons.base_sparse_field.models.fields import Serialized


class EDIExchangeConsumerMixin(models.AbstractModel):
    """Record that might have related EDI Exchange records"""

    _name = "edi.exchange.consumer.mixin"
    _description = "Abstract record where exchange records can be assigned"

    exchange_record_ids = fields.One2many(
        "edi.exchange.record",
        inverse_name="res_id",
        domain=lambda r: [("model", "=", r._name)],
    )
    exchange_record_count = fields.Integer(compute="_compute_exchange_record_count")
    expected_edi_configuration = Serialized(
        compute="_compute_expected_edi_configuration",
        default={},
    )
    has_expected_edi_configuration = fields.Boolean(
        compute="_compute_expected_edi_configuration"
    )

    def _compute_expected_edi_configuration(self):
        for record in self:
            configurations = record._get_expected_edi_configuration()
            record.expected_edi_configuration = configurations
            record.has_expected_edi_configuration = bool(configurations)

    def _get_expected_edi_configuration(self):
        exchange_types = (
            self.env["edi.exchange.type"]
            .sudo()
            .search([("model_ids.model", "=", self._name)])
        )
        result = {}
        for exchange_type in exchange_types:
            eval_ctx = dict(
                self._get_eval_context(), record=self, exchange_type=exchange_type
            )
            domain = safe_eval.safe_eval(exchange_type.enable_domain or "[]", eval_ctx)
            if not self.filtered_domain(domain):
                continue
            if exchange_type.enable_snippet:
                safe_eval.safe_eval(
                    exchange_type.enable_snippet, eval_ctx, mode="exec", nocopy=True
                )
                if not eval_ctx.get("result", False):
                    continue
            result[exchange_type.id] = exchange_type.name
        return result

    def _get_eval_context(self):
        """Prepare the context used when evaluating python code
        :returns: dict -- evaluation context given to safe_eval
        """
        return {
            "datetime": safe_eval.datetime,
            "dateutil": safe_eval.dateutil,
            "time": safe_eval.time,
            "uid": self.env.uid,
            "user": self.env.user,
        }

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        res = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        if view_type == "form":
            doc = etree.XML(res["arch"])
            for node in doc.xpath("//sheet"):
                group = False
                if hasattr(self, "_edi_generate_group"):
                    group = self._edi_generate_group
                str_element = self.env["ir.qweb"]._render(
                    "edi_oca.edi_exchange_consumer_mixin_buttons",
                    {"group": group},
                )
                node.addprevious(etree.fromstring(str_element))
            View = self.env["ir.ui.view"]

            # Override context for postprocessing
            if view_id and res.get("base_model", self._name) != self._name:
                View = View.with_context(base_model_name=res["base_model"])
            new_arch, new_fields = View.postprocess_and_fields(doc, self._name)
            res["arch"] = new_arch
            # We don't want to lose previous configuration, so, we only want to add
            # the new fields
            new_fields.update(res["fields"])
            res["fields"] = new_fields
        return res

    def _edi_create_exchange_record_vals(self, exchange_type):
        return {
            "model": self._name,
            "res_id": self.id,
        }

    def _edi_create_exchange_record(self, exchange_type, backend):
        exchange_record = backend.create_record(
            exchange_type.code, self._edi_create_exchange_record_vals(exchange_type)
        )
        self._event("on_edi_generate_manual").notify(self, exchange_record)
        return exchange_record.get_formview_action()

    def edi_create_exchange_record(self, exchange_type_id):
        self.ensure_one()
        exchange_type = self.env["edi.exchange.type"].browse(exchange_type_id)
        backend = exchange_type.backend_id
        if (
            not backend
            and self.env["edi.backend"].search_count(
                [("backend_type_id", "=", exchange_type.backend_type_id.id)]
            )
            == 1
        ):
            backend = self.env["edi.backend"].search(
                [("backend_type_id", "=", exchange_type.backend_type_id.id)]
            )
        if backend:
            return self._edi_create_exchange_record(exchange_type, backend)
        action = self.env.ref("edi_oca.edi_exchange_record_create_act_window").read()[0]
        action["context"] = {
            "default_res_id": self.id,
            "default_model": self._name,
            "default_exchange_type_id": exchange_type_id,
        }
        return action

    def _has_exchange_record(self, exchange_type, backend=False, extra_domain=False):
        """Check if there is a related exchange record following with a specific
        exchange type"""
        return bool(
            self.env["edi.exchange.record"].search_count(
                self._has_exchange_record_domain(
                    exchange_type, backend=backend, extra_domain=extra_domain
                )
            )
        )

    def _has_exchange_record_domain(
        self, exchange_type, backend=False, extra_domain=False
    ):
        domain = [
            ("model", "=", self._name),
            ("res_id", "=", self.id),
            ("type_id.code", "=", exchange_type),
        ]
        if backend:
            domain.append(("backend_id", "=", backend.id))
        if extra_domain:
            domain += extra_domain
        return domain

    def _get_exchange_record(self, exchange_type, backend=False, extra_domain=False):
        """Obtain all the exchange record related to this record with the expected
        exchange type"""

        return self.env["edi.exchange.record"].search(
            self._has_exchange_record_domain(
                exchange_type, backend=backend, extra_domain=extra_domain
            )
        )

    @api.depends("exchange_record_ids")
    def _compute_exchange_record_count(self):
        for record in self:
            record.exchange_record_count = len(record.exchange_record_ids)

    def action_view_edi_records(self):
        self.ensure_one()
        action = self.env.ref("edi_oca.act_open_edi_exchange_record_view").read()[0]
        action["domain"] = [("model", "=", self._name), ("res_id", "=", self.id)]
        return action

    @api.model
    def get_edi_access(self, doc_ids, operation, model_name=False):
        """Retrieve access policy.
        The behavior is similar to `mail.thread` and `mail.message`
        and it relies on the access rules defines on the related record.
        The behavior can be customized on the related model
        by defining `_edi_exchange_record_access`.

        By default `write`, otherwise the custom permission is returned.
        """
        DocModel = self.env[model_name] if model_name else self
        create_allow = getattr(DocModel, "_edi_exchange_record_access", "write")
        if operation in ["write", "unlink"]:
            check_operation = "write"
        elif operation == "create" and create_allow in [
            "create",
            "read",
            "write",
            "unlink",
        ]:
            check_operation = create_allow
        elif operation == "create":
            check_operation = "write"
        else:
            check_operation = operation
        return check_operation
