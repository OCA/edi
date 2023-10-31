# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from datetime import date, datetime

from dateutil.parser import parse
from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.base_wamas.models.wamas_document_field import is_date

# NOTE: At the moment, only supports these following types
FIELD_TYPES = [
    ("str", "String"),
    ("int", "Integer"),
    ("date", "Date"),
    ("time", "Time"),
]


class WamasDocumentXmlConversionTemplateMappingField(models.Model):
    _name = "wamas.document.xml.conversion.field"
    _description = "WAMAS Document XML Conversion Field"

    name = fields.Char(required=True)
    namespace = fields.Char(equired=True)
    sequence = fields.Integer(required=True, default=10)
    ttype = fields.Selection(FIELD_TYPES, "Type", default="str")
    len_field = fields.Integer("Length")
    template_id = fields.Many2one("wamas.document.xml.conversion.template")
    parent_id = fields.Many2one("wamas.document.xml.conversion.field", "Parent Node")
    element_id = fields.Many2one("wamas.document.element", "Element")
    field_id = fields.Many2one("wamas.document.field", "Field")
    df_field_template_id = fields.Many2one(
        "wamas.document.default.field.template",
        compute="_compute_df_field_template_id",
        store=True,
    )
    df_field_line_id = fields.Many2one(
        "wamas.document.default.field.template.line", "Default Field of Element"
    )
    default_value = fields.Text()
    default_func = fields.Text("Default Function")
    default_server_action_id = fields.Many2one(
        "ir.actions.server", "Default Server Action"
    )
    is_freq_element = fields.Boolean("Is Freq. Element", default=False)
    freq_element_id = fields.Many2one("wamas.document.element", "Freq. Element")
    has_attribute = fields.Boolean(default=False)

    @api.depends("element_id")
    def _compute_df_field_template_id(self):
        for rec in self:
            rec.df_field_template_id = (
                rec.element_id and rec.element_id.df_field_template_id or False
            )

    @api.onchange("element_id")
    def _onchange_element_id(self):
        self.field_id = False
        self.df_field_line_id = False

    def name_get(self):
        result = []
        for rec in self.sudo():
            name = "%s:%s" % (rec.namespace, rec.name)
            result.append((rec.id, name))
        return result

    def convert_value(self, value):
        res = value

        res = value

        if self.ttype == "str":
            res = self._set_from_string(value)
        elif self.ttype == "int":
            res = self._set_from_int(value)
        elif self.ttype == "date":
            res = self._set_from_date(value)
        elif self.ttype == "time":
            res = self._set_from_time(value)

        return res

    def _set_from_string(self, value):
        self.ensure_one()

        res = str(value)

        if self.len_field:
            res = res.ljust(self.len_field)[: self.len_field]

        return res

    def _set_from_int(self, value):
        self.ensure_one()

        try:
            res = str(int(float(value)))
        except TypeError:  # pylint: disable=except-pass
            pass

        if self.len_field:
            res = res.rjust(self.len_field, "0")[: self.len_field]

        return res

    def _set_from_date(self, value):
        self.ensure_one()

        res = value

        if isinstance(res, date):
            res = res.strftime("%Y-%m-%d")
        elif isinstance(res, datetime):
            res = res.date().strftime("%Y-%m-%d")
        elif isinstance(res, str):
            if is_date(res):
                res = parse(res).date().strftime("%Y-%m-%d")
            else:
                raise UserError(
                    _(
                        "The value '%s' is not the datetime / date type. "
                        "Please check it again!" % value
                    )
                )
        else:
            res = str(value)

        if self.len_field:
            res = res[: self.len_field]

        return res

    def _set_from_time(self, value):
        self.ensure_one()

        res = value

        if isinstance(res, date):
            res = res.strftime("%H:%M:%S")
        elif isinstance(res, datetime):
            res = res.strftime("%H:%M:%S")
        elif isinstance(res, str):
            if is_date(res):
                res = parse(res).strftime("%H:%M:%S")
            else:
                raise UserError(
                    _(
                        "The value '%s' is not the datetime / date type. "
                        "Please check it again!" % value
                    )
                )
        else:
            res = str(value)

        if self.len_field:
            res = res[: self.len_field]

        return res

    def ubl_add_item(self, items, parent_node, ns, idx=0):
        self.ensure_one()

        # Check if the element is a node or an attribute
        is_node = True
        if bool(re.search(r"\[.*?\]", self.name)):
            is_node = False

        if is_node:
            # If element is a node -> Create that node
            str_element = ns[self.namespace] + self.name
            node = etree.SubElement(parent_node, str_element)
        else:
            # If element is an attribute -> Get the parent node instead
            node = parent_node

        # Get value from `items`
        val = ""
        if self.element_id:
            if self.field_id:
                val = str(items[self.element_id.code][idx][self.field_id.code])
            elif self.df_field_line_id:
                val = str(
                    items[self.element_id.code][idx][
                        self.df_field_line_id.df_field_id.code
                    ]
                )
        elif self.default_value:
            val = str(self.default_value)
        elif self.default_func:
            val = str(getattr(self.template_id, self.default_func)())
        elif self.default_server_action_id:
            ctx = {
                "active_model": "wamas.document.xml.conversion.template",
                "active_id": self.template_id.id,
                "active_ids": [self.template_id.id],
            }
            val = self.default_server_action_id.with_context(**ctx).run()

            if val is False:
                val = ""

        val = self.convert_value(val)

        if is_node:
            # If element is a node -> Set value to that node
            node.text = val
        else:
            # If element is an attribute -> Set attribute to the parent node instead
            xml_attr = re.findall(r"\[.*?\]", self.name)[0][1:-1]
            node.set(xml_attr, val)

        return node
