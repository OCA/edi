# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class EDIExchangeInputTemplate(models.Model):
    """Define an input template to generate outgoing records' content.
    """

    _name = "edi.exchange.template.input"
    _inherit = "edi.exchange.template.mixin"
    _description = "EDI Exchange Input Template"

    input_type = fields.Char(required=True)

    def _default_code_snippet_docs(self):
        return (
            super()._default_code_snippet_docs()
            + """
        * exchange_record (edi.exchange.record)
        * record (real odoo record related to this exchange)
        * backend (current backend)
        * template (current template record)
        * utc_now
        * date_to_string
        * render_edi_template
        * get_info_provider
        * info
        """
        )

    def process_input(self, exchange_record, **kw):
        """Process for given record using related QWeb template.
        """
        # TODO

        # "exchange_record": exchange_record,
        # "record": exchange_record.record,
        # "backend": exchange_record.backend_id,
        raise NotImplementedError()

    def _get_code_snippet_eval_context(self):
        ctx = super()._get_code_snippet_eval_context()
        ctx.update({"get_data": self._get_data})
        return ctx

    def _get_data(self):
        provider = self._get_data_provider()
        if provider:
            return provider.get_data()
        return {}

    def _get_data_provider(self, exchange_record, work_ctx=None, usage=None, **kw):
        """Retrieve component providing data to process a record.

        TODO: improve this description.
        TODO: add tests
        TODO: unifye `data` provider with `info` provider
        """
        record_conf = exchange_record.type_id._component_conf_for(
            exchange_record, "process"
        )
        candidates = [self.code + ".process"]
        if record_conf:
            candidates.insert(0, record_conf["usage"])
        if usage:
            candidates.insert(0, usage)
        default_work_ctx = dict(exchange_record=exchange_record)
        default_work_ctx.update(record_conf.get("work_ctx", {}))
        default_work_ctx.update(work_ctx or {})
        provider = exchange_record.backend_id._find_component(
            candidates, work_ctx=default_work_ctx, **kw
        )
        return provider
