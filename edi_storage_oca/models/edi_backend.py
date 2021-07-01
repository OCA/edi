# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import os

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

    def _storage_cron_check_pending_input(self, **kw):
        for backend in self:
            backend._storage_check_pending_input(**kw)

    def _storage_check_pending_input(self, **kw):
        """Create new exchange records if new files found.

        Collect input exchange types and for each of them,
        check by pattern if the a new exchange record is required.
        """
        self.ensure_one()
        if not self.storage_id or not self.input_dir_pending:
            _logger.info(
                "%s ignored: no storage and/or input directory specified.", self.name
            )
            return False

        exchange_types = self.env["edi.exchange.type"].search(
            self._storage_exchange_type_pending_input_domain()
        )
        for exchange_type in exchange_types:
            # NOTE: this call might keep hanging the cron
            # if the remote storage is slow (eg: too many files)
            # We should probably run this code in a separate job per exchange type.
            file_names = self._storage_get_input_filenames(exchange_type)
            _logger.info(
                "Processing exchange type '%s': found %s files to process",
                exchange_type.display_name,
                len(file_names),
            )
            for file_name in file_names:
                self.with_delay()._storage_create_record_if_missing(
                    exchange_type, file_name
                )
        return True

    def _storage_exchange_type_pending_input_domain(self):
        """Domain for retrieving input exchange types.
        """
        return [
            ("backend_type_id", "=", self.backend_type_id.id),
            ("direction", "=", "input"),
        ]

    def _storage_create_record_if_missing(self, exchange_type, remote_file_name):
        """Create a new exchange record for given type and file name if missing.
        """
        file_name = os.path.basename(remote_file_name)
        extra_domain = [("exchange_filename", "=", file_name)]
        existing = self._find_existing_exchange_records(
            exchange_type, extra_domain=extra_domain, count_only=True
        )
        if existing:
            return
        record = self.create_record(
            exchange_type.code, self._storage_new_exchange_record_vals(file_name)
        )
        _logger.debug("%s: new exchange record generated.", self.name)
        return record.identifier

    def _storage_get_input_filenames(self, exchange_type):
        if not exchange_type.exchange_filename_pattern:
            # If there is not patter, return everything
            return self.storage_id.list_files(self.input_dir_pending)

        # TODO: validate pattern usage.
        bits = [exchange_type.exchange_filename_pattern]
        if exchange_type.exchange_file_ext:
            bits.append("*." + exchange_type.exchange_file_ext)
        pattern = "".join(bits)
        return self.storage_id.find_files(pattern, self.input_dir_pending)

    def _storage_new_exchange_record_vals(self, file_name):
        return {"exchange_filename": file_name, "edi_exchange_state": "input_pending"}
