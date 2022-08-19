# Copyright 2020 ACSONE SA
# Copyright 2020 Creu Blanca
# Copyright 2022 Camptocamp SA
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

    origin_exchange_record_id = fields.Many2one(
        string="EDI origin record",
        comodel_name="edi.exchange.record",
        ondelete="set null",
        help="EDI record that originated this document.",
    )
    exchange_record_ids = fields.One2many(
        "edi.exchange.record",
        inverse_name="res_id",
        domain=lambda r: [("model", "=", r._name)],
    )
    exchange_record_count = fields.Integer(compute="_compute_exchange_record_count")
    edi_config = Serialized(
        compute="_compute_edi_config",
        default={},
    )
    edi_has_form_config = fields.Boolean(compute="_compute_edi_config")

    def _compute_edi_config(self):
        for record in self:
            config = record._edi_get_exchange_type_config()
            record.edi_config = config
            record.edi_has_form_config = any([x.get("form") for x in config.values()])

    def _edi_get_exchange_type_config(self):
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

            result[exchange_type.id] = self._edi_get_exchange_type_conf(exchange_type)
        return result

    @api.model
    def _edi_get_exchange_type_conf(self, exchange_type):
        conf = {"form": {}}
        if exchange_type.model_manual_btn:
            conf.update({"form": {"btn": {"label": exchange_type.name}}})
        return conf

    def _get_eval_context(self):
        """Prepare context to evalue python code snippet.

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
                # TODO: add a default group
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

    def _edi_create_exchange_record(self, exchange_type, backend=None, vals=None):
        backend = exchange_type.backend_id or backend
        assert backend
        vals = vals or {}
        vals.update(self._edi_create_exchange_record_vals(exchange_type))
        return backend.create_record(exchange_type.code, vals)

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
            # FIXME: here you can still have more than one backend per type.
            # We should always get to the wizard w/ pre-populated values.
            # Maybe this behavior can be controlled by exc type adv param.
        if backend:
            exchange_record = self._edi_create_exchange_record(exchange_type, backend)
            self._event("on_edi_generate_manual").notify(self, exchange_record)
            return exchange_record.get_formview_action()
        return self._edi_get_create_record_wiz_action(exchange_type_id)

    def _edi_get_create_record_wiz_action(self, exchange_type_id):
        xmlid = "edi_oca.edi_exchange_record_create_act_window"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
        action["context"] = {
            "default_res_id": self.id,
            "default_model": self._name,
            "default_exchange_type_id": exchange_type_id,
        }
        return action

    def _has_exchange_record(self, exchange_type, backend=False, extra_domain=False):
        """Check presence of related exchange record with a specific exchange type"""
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
            ("type_id", "=", exchange_type.id),
        ]
        if backend is None:
            backend = exchange_type.backend_id
        if backend:
            domain.append(("backend_id", "=", backend.id))
        if extra_domain:
            domain += extra_domain
        return domain

    def _get_exchange_record(self, exchange_type, backend=False, extra_domain=False):
        """Get all related exchange records matching give exchange type."""
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
        xmlid = "edi_oca.act_open_edi_exchange_record_view"
        action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
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

    def _edi_set_origin(self, exc_record):
        self.sudo().update({"origin_exchange_record_id": exc_record.id})

    def _edi_get_origin(self):
        self.ensure_one()
        return self.origin_exchange_record_id
