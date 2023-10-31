# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import OrderedDict

from odoo import _, fields, models
from odoo.exceptions import UserError


def check_type_of_item(items):
    res = False

    if isinstance(items, list):
        res = "list_tuple"
    elif isinstance(items, OrderedDict):
        res = "ordered_dict"

    return res


class WamasDocumentTemplate(models.Model):
    _name = "wamas.document.template"
    _description = "WAMAS Document Template"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    line_ids = fields.One2many(
        "wamas.document.template.line", "template_id", "Lines of Elements"
    )

    def get_proper_element_from_row(self, row):
        self.ensure_one()
        res = False

        for line in self.line_ids:
            element = line.element_id

            idx_start, idx_end = element.get_index_of_field_type()

            if idx_start and idx_end:
                str_row_type = row[idx_start:idx_end]

                if str_row_type and element.code in str_row_type:
                    res = element
                    break

        return res

    def get_proper_element_from_items(self, items):
        self.ensure_one()

        res = False

        item_type = check_type_of_item(items)
        if not item_type:
            raise UserError(
                _(
                    "The input must be the list of tuples OR "
                    "the the list of ordered dictionary!"
                )
            )

        default_field_type = self.env["ir.config_parameter"].get_param(
            "wamas_document_default_field_type", "Sentence Type"
        )

        for item in items:
            if item_type == "list_tuple":
                _key = item[0]
                _value = item[1]
            elif item_type == "ordered_dict":
                _key = item
                _value = items[_key]

            if _key == default_field_type:
                found_line = self.line_ids.filtered(
                    lambda r: r.element_id.code in _value
                )

                if found_line:
                    res = found_line.element_id

        return res
