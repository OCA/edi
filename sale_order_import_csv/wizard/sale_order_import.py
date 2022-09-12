# © 2016-2017 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from tempfile import TemporaryFile

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.tools import float_compare

logger = logging.getLogger(__name__)
try:
    import unicodecsv
except ImportError:
    logger.debug("Cannot import unicodecsv")


class SaleOrderImport(models.TransientModel):
    _inherit = "sale.order.import"

    @api.model
    def parse_csv_order(self, order_file, partner):
        assert partner, "missing partner"
        fileobj = TemporaryFile("wb+")
        fileobj.write(order_file)
        fileobj.seek(0)
        reader = unicodecsv.reader(
            fileobj, delimiter=";", quoting=unicodecsv.QUOTE_MINIMAL, encoding="utf8"
        )
        i = 0
        parsed_order = {
            "partner": {"recordset": partner},
            "lines": [],
        }
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        for line in reader:
            logger.debug("csv line %d: %s", i, line)
            i += 1
            if len(line) < 2:
                raise UserError(
                    _(
                        "Error on line %d of the CSV file: this line should have "
                        "a product code and a quantity, separated by a "
                        "semi-colon."
                    )
                    % i
                )
            if not line[0]:
                raise UserError(
                    _(
                        "Error on line %d of the CSV file: the line should start "
                        "with a product code"
                    )
                    % i
                )
            try:
                qty = float(line[1])
            except:
                raise UserError(
                    _(
                        "Error on line %d of the CSV file: the second column "
                        "should contain a quantity. The quantity should use dot "
                        "as decimal separator and shouldn't have any thousand "
                        "separator"
                    )
                    % i
                )
            if float_compare(qty, 0, precision_digits=precision) != 1:
                raise UserError(
                    _(
                        "Error on line %d of the CSV file: the quantity should "
                        "be strictly positive"
                    )
                    % i
                )
            parsed_order["lines"].append(
                {
                    "qty": qty,
                    "product": {"code": line[0]},
                }
            )
        fileobj.close()
        return parsed_order
