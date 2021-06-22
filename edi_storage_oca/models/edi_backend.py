# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class EDIBackend(models.Model):

    _inherit = "edi.backend"

    storage_id = fields.Many2one(
        string="Storage backend",
        comodel_name="storage.backend",
        help="Storage for in-out files",
        ondelete="restrict",
    )
    """
    We assume the exchanges happen it 2 ways (input, output)
    and we have a hierarchy of directory like:

        from_A_to_B
            |- pending
            |- done
            |- error
        from_B_to_A
            |- pending
            |- done
            |- error

    where A and B are the partners exchanging data and they are in turn
    sender and receiver and vice versa.
    """
    # TODO: these paths should probably be by type instead
    # Here we can maybe set a common root folder for this exchange.
    input_dir_pending = fields.Char(
        "Input pending directory", help="Path to folder for pending operations"
    )
    input_dir_done = fields.Char(
        "Input done directory", help="Path to folder for doneful operations"
    )
    input_dir_error = fields.Char(
        "Input error directory", help="Path to folder for error operations"
    )
    output_dir_pending = fields.Char(
        "Output pending directory", help="Path to folder for pending operations"
    )
    output_dir_done = fields.Char(
        "Output done directory", help="Path to folder for doneful operations"
    )
    output_dir_error = fields.Char(
        "Output error directory", help="Path to folder for error operations"
    )

    _storage_actions = ("check", "send", "receive")

    def _get_component_usage_candidates(self, exchange_record, key):
        candidates = super()._get_component_usage_candidates(exchange_record, key)
        if not self.storage_id or key not in self._storage_actions:
            return candidates
        return ["storage.{}".format(key)] + candidates

    def _component_match_attrs(self, exchange_record, key):
        # Override to inject storage_backend_type
        res = super()._component_match_attrs(exchange_record, key)
        if not self.storage_id or key not in self._storage_actions:
            return res
        res["storage_backend_type"] = self.storage_id.backend_type
        return res

    def _component_sort_key(self, component_class):
        res = super()._component_sort_key(component_class)
        # Override to give precedence by storage_backend_type when needed.
        if not self.storage_id:
            return res
        return (
            1 if getattr(component_class, "_storage_backend_type", False) else 0,
        ) + res

    def _cron_check_storage_pending_input(self, **kw):
        for backend in self:
            backend._check_storage_pending_input(**kw)

    def _check_storage_pending_input(self, **kw):
        self.ensure_one()
        if not self.storage_id or not self.input_dir_pending:
            _logger.info(
                "%s ignored. No storage and/or input directory specified.", self.name
            )
            return False

        pending_files = self.storage_id.list_files(self.input_dir_pending)
        exchange_type = self.env["edi.exchange.type"].search(
            self._domain_exchange_type_storage_pending_input()
        )
        if not len(exchange_type) == 1:
            _logger.info("%s ignored. More than one exchange type found.", self.name)
            return False
        for file_name in pending_files:
            existing = self.env["edi.exchange.record"].search_count(
                [
                    ("backend_id", "=", self.id),
                    ("type_id", "=", exchange_type.id),
                    ("exchange_filename", "=", file_name),
                ]
            )
            if existing:
                continue
            self.create_record(
                exchange_type.code, self._get_exchange_record_vals(file_name)
            )
            _logger.debug("%s: new exchange record generated.", self.name)
        return True

    def _domain_exchange_type_storage_pending_input(self):
        return [
            ("backend_type_id", "=", self.backend_type_id.id),
            ("direction", "=", "input"),
        ]

    def _get_exchange_record_vals(self, file_name):
        return {"exchange_filename": file_name, "edi_exchange_state": "input_pending"}
