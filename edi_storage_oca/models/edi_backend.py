# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


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
