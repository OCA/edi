# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from pathlib import PurePath

from odoo import fields, models


class EDIExchangeType(models.Model):
    _inherit = "edi.exchange.type"

    # Extend help to explain new usage.
    exchange_filename_pattern = fields.Char(
        help="For output exchange types this should be a formatting string "
        "with the following variables available (to be used between "
        "brackets, `{}`): `exchange_record`, `record_name`, `type` and "
        "`dt`. For instance, a valid string would be "
        "{record_name}-{type.code}-{dt}\n"
        "For input exchange types related to storage backends "
        "it should be a regex expression to filter "
        "the files to be fetched from the pending directory in the related "
        "storage. E.g: `.*my-type-[0-9]*.\\.csv`"
    )

    def _storage_path(self):
        """Retrieve specific path for current exchange type.

        In your exchange type you can pass this config:

            storage:
                # simple string
                path: path/to/file

        Or

            storage:
                # name of the param containing the path
                path_config_param: path/to/file

        Thanks to the param you could even configure it by env.
        """
        self.ensure_one()
        storage_settings = self.advanced_settings.get("storage", {})
        path = storage_settings.get("path")
        if path:
            return PurePath(path)
        path_config_param = storage_settings.get("path_config_param")
        if path_config_param:
            icp = self.env["ir.config_parameter"].sudo()
            path = icp.get_param(path_config_param)
            if path:
                return PurePath(path)

    def _storage_fullpath(self, directory=None, filename=None):
        self.ensure_one()
        path_prefix = self._storage_path()
        path = PurePath((directory or "").strip().rstrip("/"))
        if path_prefix:
            path = path_prefix / path
        if filename:
            path = path / filename.strip("/")
        return path
