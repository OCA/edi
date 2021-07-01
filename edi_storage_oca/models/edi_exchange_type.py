# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

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
