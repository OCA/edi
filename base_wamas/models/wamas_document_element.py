# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import OrderedDict

from odoo import _, fields, models
from odoo.exceptions import UserError

from ..models.wamas_document_template import check_type_of_item


def get_item(recordset_field, row, idx_start, res, convert_type):
    for field in recordset_field:
        if field._name == "wamas.document.default.field.template.line":
            field = field.df_field_id

        idx_end = idx_start + field.len_field

        val = row[idx_start:idx_end]
        if convert_type:
            val = field.get_value_from_string(val)

        if isinstance(res, OrderedDict):
            res[field.code] = val
        elif isinstance(res, list):
            res.append((field.code, val))

        idx_start = idx_end

    return res, idx_start


class WamasDocumentElement(models.Model):
    _name = "wamas.document.element"
    _description = "WAMAS Document Element"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    df_field_template_id = fields.Many2one(
        "wamas.document.default.field.template", "Default Field Template", required=True
    )
    field_ids = fields.One2many("wamas.document.field", "element_id", "Fields")

    def get_values_from_element(
        self, row, convert_type=False, result_type="ordered_dict"
    ):
        self.ensure_one()

        res = False

        if result_type == "list_tuple":
            res = []
        elif result_type == "ordered_dict":
            res = OrderedDict()
        idx = 0

        # Get value from `row` for `default fields`
        sorted_fields = self.df_field_template_id.line_ids.sorted(
            key=lambda r: r.sequence
        )
        res, idx = get_item(sorted_fields, row, idx, res, convert_type)

        # Get value from `row` for `fields`
        sorted_fields = self.field_ids.sorted(key=lambda r: r.sequence)
        res, idx = get_item(sorted_fields, row, idx, res, convert_type)

        return res

    def set_values_to_element(self, items):
        self.ensure_one()

        res = ""

        item_type = check_type_of_item(items)
        if not item_type:
            raise UserError(
                _(
                    "The input must be the list of tuples OR "
                    "the the list of ordered dictionary!"
                )
            )

        for item in items:
            if item_type == "list_tuple":
                _key = item[0]
                _value = item[1]
            elif item_type == "ordered_dict":
                _key = item
                _value = items[_key]

            for line in self.df_field_template_id.line_ids:
                df_field = line.df_field_id

                if _key == df_field.code:
                    res += df_field.set_value_to_string(_value)

            for field in self.field_ids:
                if _key == field.code:
                    a1 = field.set_value_to_string(_value)
                    res += a1

        return res

    def get_index_of_field_type(self):
        self.ensure_one()

        idx_start = False
        idx_end = False

        default_field_type = self.env["ir.config_parameter"].get_param(
            "wamas_document_default_field_type", "Sentence Type"
        )
        line_of_field_type = self.df_field_template_id.line_ids.filtered(
            lambda r: r.df_field_id.code == default_field_type
        )

        if line_of_field_type:
            field_type = line_of_field_type.df_field_id

            filtered_lines = self.df_field_template_id.line_ids.filtered(
                lambda r: r.sequence < line_of_field_type.sequence
            )

            if filtered_lines:
                idx_start = sum([line.df_field_id.len_field for line in filtered_lines])
                idx_end = idx_start + field_type.len_field

        return idx_start, idx_end
