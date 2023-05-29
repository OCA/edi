# Copyright 2022 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, models
from odoo.tools import frozendict

_logger = logging.getLogger("edi_exchange_auto")


class EDIAutoExchangeConsumerMixin(models.AbstractModel):
    """Enhance edi.exchange.consumer.mixin behavior to automatize actions."""

    _name = "edi.auto.exchange.consumer.mixin"
    _inherit = "edi.exchange.consumer.mixin"
    _description = __doc__

    @api.model
    def _edi_get_exchange_type_conf(self, exchange_type):
        conf = super()._edi_get_exchange_type_conf(exchange_type)
        auto_conf = exchange_type.get_settings().get("auto", {}).get(self._name, {})
        conf.update({"auto": auto_conf})
        return conf

    """Disable automatic EDI programmatically on models.
    """  # pylint: disable=pointless-string-statement
    _edi_no_auto_for_operation = (
        # "create",
        # "write",
        # "unlink",
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        todo = None
        operation = "create"
        candidates = self.browse()
        for rec in records:
            if not rec._edi_auto_skip(operation):
                candidates |= rec
        if candidates:
            todo = candidates._edi_auto_collect_todo(operation, vals_list)
        if todo:
            # TODO: schedule call on post commit
            candidates._edi_auto_handle(todo)
        return rec

    def write(self, vals):
        todo = None
        operation = "write"
        candidates = self.browse()
        for rec in self:
            if not rec._edi_auto_skip(operation):
                candidates |= rec
        if candidates:
            todo_vals = [vals.copy() for x in candidates]
            todo = candidates._edi_auto_collect_todo(operation, todo_vals)
        res = super().write(vals)
        if todo:
            candidates._edi_auto_handle(todo)
        return res

    # TODO
    # def unlink(self):

    def _edi_auto_skip(self, operation):
        skip_reason = None
        if self.env.context.get("edi__skip_auto_handle"):
            skip_reason = "edi__skip_auto_handle ctx key found"
        elif operation in self._edi_no_auto_for_operation:
            skip_reason = f"{operation} disabled attr _edi_no_auto_for_operation"
        elif self.disable_edi_auto:
            skip_reason = f"EDI auto disabled for rec={self.id}"
        if skip_reason:
            self._edi_auto_log_skip(operation, skip_reason)
            return True
        return False

    def _edi_auto_collect_todo(self, operation, new_vals_list):
        """Generate list of automatic actions to do.

        :param operation: valid edi action (see ``edi.backend._is_valid_edi_action``)
        :param new_vals: list of new values for current record(s)
        """
        res = []
        # auto:
        #   "model.to.handle":
        #     actions:
        #       generate:
        #         when:
        #           - create
        #           - write
        #           - unlink
        #         if:
        #           - domain: $domain TODO: support domain
        #           - callable: $callable_on_model
        #         event_only: false
        #         force: true
        #         target_record: order_id
        #         trigger_fields:
        #           - state
        #           - order_line
        #         tracked_fields:
        #           - state
        #           - expected_date
        #
        rec_by_type = self._edi_auto_collect_records_by_type(operation, new_vals_list)
        for exc_type, data in rec_by_type.items():
            conf = data["conf"]
            records = data["records"]
            new_vals = data["new_vals"]
            if not exc_type.backend_id:
                # TODO: add validation on adv settings?
                skip_reason = f"Backend required, not set on type={exc_type.code}"
                self._edi_auto_log_skip(operation, skip_reason, exc_type=exc_type)
                continue
            backend = exc_type.backend_id
            for action_name, action_conf in conf.get("actions", {}).items():
                if not backend._is_valid_edi_action(action_name):
                    skip_reason = f"EDI action not allowed ={action_name}"
                    self._edi_auto_log_skip(operation, skip_reason, exc_type=exc_type)
                    continue
                if operation not in action_conf.get("when", []):
                    skip_reason = f"Operation not allowed for action={action_name}"
                    self._edi_auto_log_skip(operation, skip_reason, exc_type=exc_type)
                    continue
                triggers = action_conf.get("trigger_fields", [])
                if not triggers:
                    skip_reason = f"No trigger set for action={action_name}"
                    self._edi_auto_log_skip(operation, skip_reason, exc_type=exc_type)
                    continue
                tracked = action_conf.get("tracked_fields", [])
                trigger = None
                for k in triggers:
                    if k in new_vals:
                        trigger = k
                        break
                if trigger:
                    if trigger not in tracked:
                        tracked.append(trigger)
                    checker = None
                    if action_conf.get("if", {}).get("callable"):
                        callable_name = action_conf["if"]["callable"]
                        try:
                            checker = getattr(self, callable_name)
                        except AttributeError:
                            skip_reason = f"Invalid callable={callable_name}"
                            self._edi_auto_log_skip(
                                operation, skip_reason, exc_type=exc_type
                            )
                            continue
                    vals = frozendict(
                        {k: v for k, v in new_vals.items() if k in tracked}
                    )
                    # TODO: group by record in case `target_record` is different
                    # or let it trigger N exchanges for sub models?
                    for rec in records:
                        target_record = self._edi_auto_get_target_record(
                            rec, action_conf
                        )
                        old_vals = frozendict({k: rec[k] for k in tracked})
                        todo = self._edi_auto_prepare_info(
                            edi_type=exc_type,
                            edi_action=action_name,
                            conf=action_conf,
                            triggered_by=trigger,
                            record=rec,
                            target_record=target_record,
                            vals=vals,
                            old_vals=old_vals,
                            force=action_conf.get("force", False),
                            event_only=action_conf.get("event_only", False),
                        )
                        if checker and not checker(todo):
                            skip_reason = (
                                f"Checker {checker.__func__.__name__} skip action"
                            )
                            self._edi_auto_log_skip(
                                operation, skip_reason, exc_type=exc_type
                            )
                            continue
                        res.append(todo)
        return res

    def _edi_auto_collect_records_by_type(self, operation, new_vals_list):
        skip_type_ids = set()
        rec_by_type = {}
        for rec, new_vals in zip(self, new_vals_list):
            for type_id, conf in rec.edi_config.items():
                if type_id in skip_type_ids:
                    continue
                exc_type = self.env["edi.exchange.type"].browse(int(type_id))
                # Get auto conf for current model
                auto_conf = conf.get("auto", {})
                actions = auto_conf.get("actions", {})
                skip_reason = None
                if not auto_conf or auto_conf.get("disable"):
                    skip_reason = "Auto-conf not found or disabled"
                elif not actions:
                    skip_reason = "Auto-conf has no action configured"
                if skip_reason:
                    skip_type_ids.add(type_id)
                    self._edi_auto_log_skip(operation, skip_reason, exc_type=exc_type)
                    continue
                if type_id not in rec_by_type:
                    rec_by_type[exc_type] = {
                        "conf": auto_conf,
                        "records": [],
                        "new_vals": new_vals,
                    }
                rec_by_type[exc_type]["records"].append(rec)
        return rec_by_type

    def _edi_auto_log_skip(self, operation, reason, exc_type=None):
        log_msg = "Skip model=%(model)s op=%(op)s"
        log_args = {
            "model": self._name,
            "op": operation,
            "reason": reason,
        }
        if exc_type:
            log_msg += " type=%(type_code)s"
            log_args["type_code"] = exc_type.code
        log_msg += ": %(reason)s"
        _logger.debug(log_msg, log_args)

    def _edi_auto_get_target_record(self, rec, action_conf):
        target_record = rec
        mapped = action_conf.get("target_record")
        if mapped:
            target_record = rec.mapped(mapped)
        return target_record

    def _edi_auto_prepare_info(self, **kw):
        kw["edi_type_id"] = kw.pop("edi_type").id
        record = kw.pop("record")
        target_record = kw.pop("target_record")
        kw["_records"] = {
            "source": {
                "model": record._name,
                "id": record.id,
            },
            "target": {
                "model": target_record._name,
                "id": target_record.id,
            },
        }
        # TODO: serialize old_vals in case of relations
        return EDIAutoInfo(**kw)

    def _edi_auto_handle(self, todo):
        """Handle automatic EDI actions to do.

        :param todo: list of `EDIAutoInfo` objects
        """
        for info in todo:
            edi_action = info.edi_action
            target_record = info.get_target_record(self.env)
            if info.event_only:
                target_record._edi_auto_trigger_event(target_record, info)
                continue
            job_options = target_record._edi_auto_handle_job_options(info)
            handler = getattr(
                target_record.with_delay(**job_options),
                "_edi_auto_handle_" + edi_action,
                None,
            )
            if not handler:
                raise NotImplementedError(f"{edi_action} handler not implemented yet")
            handler(info.as_dict())

    def _edi_auto_handle_job_options(self, info):
        return {}

    # TODO: Define job identity_key
    # so that we don't create multiple records on multiple edits.
    # This is tied to the problem of avoiding too many jobs to be created.
    # For instance: how do we prevent to generate 10 exports
    # when 10 sale order lines are updated one after each other?
    def _edi_auto_handle_generate(self, info_dict):
        info = EDIAutoInfo.from_dict(info_dict)
        target_record = info.get_target_record(self.env)
        exc_type = info.get_type(self.env)
        exchange_record = self._edi_auto_get_or_create_record(target_record, exc_type)
        exchange_record.action_exchange_generate()
        msg = _("EDI auto: output generated.")
        trigger_msg = _("Triggered by: %s") % info.triggered_by
        # TODO: post changed values in msg?
        exchange_record._notify_related_record(msg + "\n" + trigger_msg)
        # Trigger event on exchange record
        exchange_record._trigger_edi_event("generated", suffix="auto", info=info)
        # Trigger event on current record
        self._edi_auto_trigger_event(target_record, info)

    def _edi_auto_get_or_create_record(self, target_record, exchange_type):
        # TODO: here we must filter acks that are not valued yet.
        # We should take control via conf on
        # wether the ack has to be generated immediately or not
        # by the cron of the backend.
        parent = target_record._edi_get_origin()
        exchange_record = target_record._get_exchange_record(exchange_type).filtered(
            lambda x: not x.exchange_file
        )
        if not exchange_record:
            vals = exchange_record._exchange_child_record_values()
            vals["parent_id"] = parent.id
            exchange_record = target_record._edi_create_exchange_record(
                exchange_type, vals=vals
            )
        return exchange_record

    def _edi_auto_trigger_event(self, target_record, info):
        self._event(self._edi_auto_make_event_name(info)).notify(
            target_record, info=info
        )

    def _edi_auto_make_event_name(self, info):
        return f"on_edi_auto_{info.edi_action}"


class EDIAutoInfo:
    """Serialize-able object holding info on automatic actions and events."""

    __slots__ = (
        "edi_type_id",
        "edi_action",
        "conf",
        "triggered_by",
        "_records",
        "vals",
        "old_vals",
        "force",
        "event_only",
    )

    def __init__(self, **kw):
        for k, v in kw.items():
            if k in self.__slots__:
                setattr(self, k, v)

    def as_dict(self):
        return {k: getattr(self, k) for k in self.__slots__}

    @classmethod
    def from_dict(cls, vals):
        return cls(**vals)

    def get_type(self, env):
        return env["edi.exchange.type"].browse(self.edi_type_id)

    def get_record(self, env):
        source = self._records["source"]
        return env[source["model"]].browse(source["id"])

    def get_target_record(self, env):
        target = self._records["target"]
        return env[target["model"]].browse(target["id"])
