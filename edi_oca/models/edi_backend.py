# Copyright 2020 ACSONE SA
# Copyright 2020 Creu Blanca
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import base64
import logging

from odoo import _, exceptions, fields, models, tools

from odoo.addons.component.exception import NoComponentError

_logger = logging.getLogger(__name__)


class EDIBackend(models.Model):
    """Generic backend to control EDI exchanges.

    Backends can be organized with types.

    The backend should be responsible for generating export records.
    For each record it can generate or parse their values
    depending on their direction (incoming, outgoing).
    """

    _name = "edi.backend"
    _description = "EDI Backend"
    _inherit = ["collection.base"]

    name = fields.Char(required=True)
    backend_type_id = fields.Many2one(
        string="EDI Backend type",
        comodel_name="edi.backend.type",
        required=True,
        ondelete="restrict",
    )

    def _get_component(self, usage_candidates, safe=True, work_ctx=None, **kw):
        """Retrieve components for current backend.

        :param usage_candidates:
            list of usage to try by priority. 1st found, 1st returned
        :param safe: boolean, if true does not break if component is not found
        :param work_ctx: dictionary with work context params
        :param kw: keyword args to lookup for components (eg: usage)
        """
        component = None
        work_ctx = work_ctx or {}
        if "backend" not in work_ctx:
            work_ctx["backend"] = self
        with self.work_on(self._name, **work_ctx) as work:
            for usage in usage_candidates:
                component = work.many_components(usage=usage, **kw)
                if component:
                    return component[0]
        if not component and not safe:
            raise NoComponentError(
                "No componend found matching any of: {}".format(usage_candidates)
            )
        return component or None

    @property
    def exchange_record_model(self):
        return self.env["edi.exchange.record"]

    def create_record(self, type_code, values):
        """Create an exchange record for current backend.

        :param type_code: edi.exchange.type code
        :param values: edi.exchange.record values
        :return: edi.exchange.record record
        """
        self.ensure_one()
        _values = self._create_record_prepare_values(type_code, values)
        return self.exchange_record_model.create(_values)

    def _create_record_prepare_values(self, type_code, values):
        res = values.copy()  # do not pollute original dict
        export_type = self.env["edi.exchange.type"].search(
            self._get_exchange_type_domain(type_code), limit=1
        )
        export_type.ensure_one()
        res["type_id"] = export_type.id
        res["backend_id"] = self.id
        return res

    def _get_exchange_type_domain(self, code):
        return [
            ("code", "=", code),
            "|",
            ("backend_type_id", "=", self.backend_type_id.id),
            ("backend_id", "=", self.id),
        ]

    def generate_output(self, exchange_record, store=True, force=False, **kw):
        """Generate output content for given exchange record.

        :param exchange_record: edi.exchange.record recordset
        :param store: store output on the record itself
        :param force: allow to re-genetate the content
        :param kw: keyword args to be propagated to output generate handler
        """
        self.ensure_one()
        self._validate_generate_output(exchange_record, force=force)
        output = self._generate_output(exchange_record, **kw)
        if output and store:
            if not isinstance(output, bytes):
                output = output.encode()
            exchange_record.update(
                {
                    "exchange_file": base64.b64encode(output),
                    "edi_exchange_state": "output_pending",
                }
            )
        return tools.pycompat.to_text(output)

    def _validate_generate_output(self, exchange_record, force=False):
        exchange_record.ensure_one()
        if (
            exchange_record.edi_exchange_state != "new"
            and exchange_record.exchange_file
            and not force
        ):
            raise exceptions.UserError(
                _(
                    "Exchange record ID=%d is not in draft state "
                    "and has already an output value."
                )
                % exchange_record.id
            )
        if not exchange_record.direction != "outbound":
            raise exceptions.UserError(
                _("Exchange record ID=%d is not file is not meant to b generated")
                % exchange_record.id
            )
        if exchange_record.exchange_file:
            raise exceptions.UserError(
                _("Exchabge record ID=%d already has a file to process!")
                % exchange_record.id
            )

    def _generate_output(self, exchange_record, **kw):
        # TODO: maybe lookup for an `exchange_record.model` specific component 1st
        candidates = self._get_component_usage_candidates(exchange_record, "generate")
        component = self._get_component(
            candidates, work_ctx={"exchange_record": exchange_record}
        )
        if component:
            return component.generate()
        raise NotImplementedError("No handler for `_generate_output`")

    def _get_component_usage_candidates(self, exchange_record, key):
        """Retrieve usage candidates for components."""
        # fmt:off
        base_usage = ".".join([
            "edi",
            exchange_record.direction,
            key,
            self.backend_type_id.code,
        ])
        # fmt:on
        type_code = exchange_record.type_id.code
        return [
            # specific for backend type and exchange type
            base_usage + "." + type_code,
            # specific for backend type
            base_usage,
        ]

    # TODO: add job config for these methods
    def exchange_send(self, exchange_record):
        """Send exchange file."""
        self.ensure_one()
        exchange_record.ensure_one()
        # In case already sent: skip sending and check the state
        check = self._output_check_send(exchange_record)
        if not check:
            return False
        state = exchange_record.edi_exchange_state
        error = False
        message = None
        try:
            self._exchange_send(exchange_record)
        except self._swallable_exceptions() as err:
            if self.env.context.get("_edi_send_break_on_error"):
                raise
            error = repr(err)
            state = "output_error_on_send"
            message = exchange_record._exchange_status_message("send_ko")
            res = False
        else:
            # TODO: maybe the send handler should return desired message and state
            message = exchange_record._exchange_status_message("send_ok")
            error = None
            state = "output_sent"
            res = True
        finally:
            exchange_record.write(
                {
                    "edi_exchange_state": state,
                    "exchange_error": error,
                    # FIXME: this should come from _compute_exchanged_on
                    # but somehow it's failing in send tests (in record tests it works).
                    "exchanged_on": fields.Datetime.now(),
                }
            )
            if message:
                self._exchange_notify_record(exchange_record, message)
        return res

    def _swallable_exceptions(self):
        # TODO: improve this list
        return (
            ValueError,
            FileNotFoundError,
            exceptions.UserError,
            exceptions.ValidationError,
        )

    def _output_check_send(self, exchange_record):
        if exchange_record.direction != "output":
            raise exceptions.UserError(
                _("Record ID=%d is not meant to be sent!") % exchange_record.id
            )
        if not exchange_record.exchange_file:
            raise exceptions.UserError(
                _("Record ID=%d has no file to send!") % exchange_record.id
            )
        return exchange_record.edi_exchange_state in [
            "output_pending",
            "output_error_on_send",
        ]

    def _exchange_send(self, exchange_record):
        # TODO: maybe lookup for an `exchange_record.model` specific component 1st
        candidates = self._get_component_usage_candidates(exchange_record, "send")
        component = self._get_component(
            candidates, work_ctx={"exchange_record": exchange_record}
        )
        if component:
            return component.send()
        raise NotImplementedError("No handler for `_exchange_send`")

    def _exchange_notify_record(self, exchange_record, message, level="info"):
        """Attach notification of exchange state to the original record."""
        if not hasattr(exchange_record.record, "message_post_with_view"):
            return
        exchange_record.record.message_post_with_view(
            "edi.message_edi_exchange_link",
            values={
                "backend": self,
                "exchange_record": exchange_record,
                "message": message,
                "level": level,
            },
            subtype_id=self.env.ref("mail.mt_note").id,
        )

    def _cron_check_output_exchange_sync(self, **kw):
        for backend in self:
            backend._check_output_exchange_sync(**kw)

    def _check_output_exchange_sync(self, skip_send=False):
        """Lookup for pending output records and take care of them.

        First work on records that need output generation.
        Then work on records waiting for a state update.

        :param skip_send: only generate missing output.
        """
        # Generate output files
        new_records = self.exchange_record_model.search(
            self._output_new_records_domain()
        )
        _logger.info(
            "EDI Exchange output sync: found %d new records to process.",
            len(new_records),
        )
        for rec in new_records:
            self.generate_output(rec)

        if skip_send:
            return
        pending_records = self.exchange_record_model.search(
            self._output_pending_records_domain()
        )
        _logger.info(
            "EDI Exchange output sync: found %d pending records to process.",
            len(pending_records),
        )
        for rec in pending_records:
            if rec.edi_exchange_state == "output_pending":
                self.exchange_send(rec)
            else:
                self._exchange_output_check_state(rec)

    def _output_new_records_domain(self):
        return [
            ("backend_id", "=", self.id),
            ("type_id.exchange_file_auto_generate", "=", True),
            ("type_id.direction", "=", "output"),
            ("edi_exchange_state", "=", "new"),
            ("exchange_file", "=", False),
        ]

    def _output_pending_records_domain(self):
        states = ("output_pending", "output_sent", "output_sent_and_error")
        return [
            ("type_id.direction", "=", "output"),
            ("backend_id", "=", self.id),
            ("edi_exchange_state", "in", states),
        ]

    def _exchange_output_check_state(self, exchange_record):
        # TODO: maybe lookup for an `exchange_record.model` specific component 1st
        candidates = self._get_component_usage_candidates(exchange_record, "check")
        component = self._get_component(
            candidates, work_ctx={"exchange_record": exchange_record}
        )
        if component:
            return component.check()
        raise NotImplementedError("No handler for `_exchange_output_check_state`")

    def _trigger_edi_event_make_name(self, exchange_record, name, suffix=None):
        return "on_edi_exchange_{name}{suffix}".format(
            name=name, suffix=("_" + suffix) if suffix else "",
        )

    def _trigger_edi_event(self, exchange_record, name, suffix=None):
        """Trigger a component event linked to this backend and edi exchange."""
        name = self._trigger_edi_event_make_name(exchange_record, name, suffix=suffix)
        self._event(name).notify(exchange_record)

    def _notify_done(self, exchange_record):
        self._exchange_notify_record(
            exchange_record, exchange_record._exchange_status_message("process_ok")
        )
        self._trigger_edi_event(exchange_record, "done")

    def _notify_error(self, exchange_record, message_key):
        self._exchange_notify_record(
            exchange_record,
            exchange_record._exchange_status_message(message_key),
            level="error",
        )
        self._trigger_edi_event(exchange_record, "error")

    def _notify_ack_received(self, exchange_record):
        self._exchange_notify_record(
            exchange_record, exchange_record._exchange_status_message("ack_received")
        )
        self._trigger_edi_event(exchange_record, "done", suffix="ack_received")

    def _notify_ack_missing(self, exchange_record):
        self._exchange_notify_record(
            exchange_record,
            exchange_record._exchange_status_message("ack_missing"),
            level="warning",
        )
        self._trigger_edi_event(exchange_record, "done", suffix="ack_missing")

    def _notify_ack_received_error(self, exchange_record):
        self._exchange_notify_record(
            exchange_record,
            exchange_record._exchange_status_message("ack_received_error"),
        )
        self._trigger_edi_event(exchange_record, "done", suffix="ack_received_error")

    def _exchange_input_check(self, exchange_record):
        if not exchange_record.direction == "input":
            raise exceptions.UserError(
                _("Record ID=%d is not meant to be processed") % exchange_record.id
            )
        if not exchange_record.exchange_file:
            raise exceptions.UserError(
                _("Record ID=%d has no file to process!") % exchange_record.id
            )
        return exchange_record.edi_exchange_state in [
            "input_received",
            "input_processed_error",
        ]

    def exchange_process(self, exchange_record):
        """Process an incoming document.

        This function should be called when an exchange record has been received
        it could integrate check where to relate or modificate the data
        """
        self.ensure_one()
        exchange_record.ensure_one()
        # In case already processed: skip processing and check the state
        check = self._exchange_input_check(exchange_record)
        if not check:
            return False
        try:
            self._exchange_process(exchange_record)
        except self._swallable_exceptions() as err:
            if self.env.context.get("_edi_receive_break_on_error"):
                raise
            error = repr(err)
            state = "input_processed_error"
            message = exchange_record._exchange_status_message("process_ko")
            res = False
        else:
            message = exchange_record._exchange_status_message("process_ok")
            error = None
            state = "input_processed"
            res = True
        finally:
            exchange_record.write(
                {
                    "edi_exchange_state": state,
                    "exchange_error": error,
                    # FIXME: this should come from _compute_exchanged_on
                    # but somehow it's failing in send tests (in record tests it works).
                    "exchanged_on": fields.Datetime.now(),
                }
            )
            if message:
                self._exchange_notify_record(exchange_record, message)
        return res

    def _exchange_process(self, exchange_record):
        # TODO: maybe lookup for an `exchange_record.model` specific component 1st
        candidates = self._get_component_usage_candidates(exchange_record, "process")
        component = self._get_component(
            candidates, work_ctx={"exchange_record": exchange_record}
        )
        if component:
            return component.process()
        raise NotImplementedError()
