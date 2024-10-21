# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import re
from datetime import datetime

from odoo import _, api, fields, models


class BaseImportPdfTemplate(models.Model):
    _name = "base.import.pdf.template"
    _description = "Base Import Pdf Template"
    _order = "name desc"

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    extraction_mode = fields.Selection(
        selection=[("pypdf", "Pypdf")],
        default="pypdf",
        string="Extraction mode",
    )
    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Main Model",
        domain=[("transient", "=", False), ("model", "not like", "base.import.pdf")],
        required=True,
        ondelete="cascade",
    )
    model = fields.Char(compute="_compute_model", store=True, compute_sudo=True)
    child_field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        string="Child Field",
        domain="[('model_id.model', '=', model), ('ttype', '=', 'one2many')]",
        ondelete="cascade",
    )
    child_model = fields.Char(
        compute="_compute_child_model", store=True, compute_sudo=True
    )
    child_field_name = fields.Char(related="child_field_id.name")
    auto_detect_pattern = fields.Char(
        string="Auto detect pattern",
        help="""It will be necessary to set a patter that only finds something
        in the documents for this template.""",
    )
    header_items = fields.Char(help="Header columns separated by commas")
    company_id = fields.Many2one(comodel_name="res.company", string="Company")
    line_ids = fields.One2many(
        comodel_name="base.import.pdf.template.line",
        inverse_name="template_id",
        copy=True,
    )

    @api.depends("model_id")
    def _compute_model(self):
        for item in self.filtered("model_id"):
            item.model = item.model_id.model

    @api.depends("child_field_id")
    def _compute_child_model(self):
        for item in self.filtered("child_field_id"):
            item.child_model = item.child_field_id.relation

    def button_preview(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "base_import_pdf_by_template.action_wizard_base_import_pdf_preview"
        )
        ctx = self._context.copy()
        ctx.update({"default_extraction_mode": self.extraction_mode})
        action["context"] = ctx
        return action

    def _get_items_from_model(self, model):
        return self.search(
            [
                ("company_id", "in", [False] + self.env.companies.ids),
                ("model", "=", model),
            ]
        )

    def _auto_detect_from_text(self, text):
        """Look for if any of the templates find the pattern in the text."""
        for item in self.filtered("auto_detect_pattern"):
            if text and re.findall(item.auto_detect_pattern, text):
                return item
        return False

    def _get_table_info(self, text):
        """Convert table data to a readable dict."""
        res = False
        if text and self.header_items:
            res = {"header": self.header_items, "data": []}
            data = self._get_table_info_data(text)
            res["data"].extend(data)
        return res

    def _get_table_info_data(self, text):
        """Set table using lines: column + pattern (groups)."""
        data = []
        data_map_column = {}
        child_lines = self.line_ids.filtered(
            lambda x: x.related_model == "lines"
            and x.value_type != "fixed"
            and x.pattern
        )
        for child_line in child_lines:
            data_column = []
            matches = re.finditer(child_line.pattern, text, re.MULTILINE)
            for _matchNum, match in enumerate(matches, start=1):
                match_group = match.groups(0)[0]
                data_column.append(match_group.strip())
            data_map_column[int(child_line.column)] = data_column
        # Convert data column to lines (table lines "split" in pages not supported)
        data_keys = list(data_map_column.keys())
        data_key_0 = data_keys[0]
        for x in range(len(data_map_column[data_key_0])):
            line_data = []
            for data_key in data_keys:
                total_items = len(data_map_column[data_key]) - 1
                if total_items >= x:
                    line_data.append(data_map_column[data_key][x])
            data.append(line_data)
        return data

    def _prepare_ctx_from_model(self, model):
        ctx = dict(self.env.context)
        fixed_fields = self._get_fixed_fields_from_model(model)
        for fixed_key in list(fixed_fields.keys()):
            ctx_key = "default_%s" % fixed_key
            fixed_value = fixed_fields[fixed_key]
            if isinstance(fixed_value, models.Model):
                fixed_value = fixed_value.id
            ctx.update({ctx_key: fixed_value})
        return ctx

    def _get_fixed_fields_from_model(self, model):
        res = {}
        fixed_fields = self.line_ids.filtered(
            lambda x: x.model == model and x.value_type == "fixed"
        )
        for fixed_field in fixed_fields:
            res[fixed_field.field_name] = fixed_field._get_fixed_value()
        return res

    def _get_field_header_values(self, text):
        return self._get_field_values("header", text)

    def _get_field_child_values(self, table_info):
        """Process the information from the _get_table_info() method.."""
        res = []
        if table_info and table_info["data"]:
            for data_line in table_info["data"]:
                res_line = self._get_field_values_from_table_item(data_line)
                if res_line:
                    res.append(res_line)
        return res

    def _get_field_values_from_table_item(self, item):
        res = False
        child_lines = self.line_ids.filtered(
            lambda x: x.related_model == "lines"
            and x.value_type != "fixed"
            and x.column
        )
        if item and child_lines:
            item_lenght = len(item) - 1
            res = {}
            for child_line in child_lines:
                column = int(child_line.column)
                if item_lenght >= column and item[column]:
                    value = child_line._process_value(item[column])
                    res[child_line.field_name] = value
        return res

    def _get_field_values(self, related_model, text):
        res = {}
        for field in self.line_ids.filtered(
            lambda x: x.related_model == related_model and x.value_type != "fixed"
        ):
            value = field._get_field_value(text)
            if value:
                res[field.field_name] = value
        return res


class BaseImportPdfTemplateLine(models.Model):
    _name = "base.import.pdf.template.line"
    _description = "Base Import Pdf Template Line"
    _order = "model asc, id"

    template_id = fields.Many2one(
        comodel_name="base.import.pdf.template",
        string="Template",
        required=True,
        ondelete="cascade",
    )
    related_model = fields.Selection(
        selection=[("header", _("Header")), ("lines", _("Lines"))],
        default="header",
        string="Related model",
    )
    model = fields.Char(compute="_compute_model", store=True)
    field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        string="Field",
        domain="[('model_id.model', '=', model), ('store', '=', True)]",
        required=True,
        ondelete="cascade",
    )
    field_name = fields.Char(related="field_id.name")
    field_ttype = fields.Selection(related="field_id.ttype")
    field_relation = fields.Char(related="field_id.relation")
    column = fields.Char()
    pattern = fields.Char()
    search_field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        domain="[('model_id.model', '=', field_relation)]",
        string="Search field",
    )
    search_field_name = fields.Char(
        related="search_field_id.name", string="Search field name"
    )
    search_field_ttype = fields.Selection(
        related="search_field_id.ttype", string="Search field type"
    )
    search_field_relation = fields.Char(
        related="search_field_id.relation", string="Search field relation"
    )
    search_subfield_id = fields.Many2one(
        comodel_name="ir.model.fields",
        domain="[('model_id.model', '=', search_field_relation)]",
        string="Search subfield",
    )
    default_value = fields.Reference(
        selection="_selection_reference_value",
        string="Default value",
    )
    date_format = fields.Selection(
        selection=[
            ("*Y-*d-*m", _("YY-dd-MM")),
            ("*m-*d-*Y", _("MM-dd-YY")),
            ("*Y/*d/*m", _("YY/dd/MM")),
            ("*m/*d/*Y", _("MM/dd/YY")),
            ("*d.*m.*Y", _("dd.MM.YY")),
            ("*d/*m/*Y", _("dd/MM/YY")),
            ("*d/*m/*y-short", _("dd/MM/yy")),
            ("*B *d, *Y", _("B d, YY")),
        ],
    )
    time_format = fields.Selection(
        selection=[
            ("*H:*M:*S", _("H:M:S")),
        ],
    )
    decimal_separator = fields.Selection(
        selection=[
            ("dot", "Dot (.)"),
            ("comma", "Comma (,)"),
        ],
        default="dot",
    )
    thousand_separator = fields.Selection(
        selection=[
            ("none", _("None")),
            ("space", _("Space ( )")),
            ("dot", _("Dot (.)")),
            ("comma", _("Comma (,)")),
        ],
        default="none",
    )
    log_distinct_value = fields.Boolean(
        string="Log distint value?",
        help="""A note will be added with the previous value and the indicated value if
        they are different.""",
    )
    value_type = fields.Selection(
        selection=[
            ("fixed", _("Fixed")),
            ("variable", _("Variable")),
        ],
        default="variable",
        string="Value type",
    )
    fixed_value_char = fields.Char()
    fixed_value_date = fields.Date()
    fixed_value_datetime = fields.Datetime()
    fixed_value_float = fields.Float()
    fixed_value_html = fields.Html()
    fixed_value_integer = fields.Integer()
    fixed_value_selection = fields.Many2one(
        comodel_name="ir.model.fields.selection", domain="[('field_id', '=', field_id)]"
    )
    fixed_value_text = fields.Text()
    fixed_value = fields.Reference(
        selection="_selection_reference_value",
        string="Fixed value",
    )
    mapped_ids = fields.One2many(
        comodel_name="base.import.pdf.template.line.mapped",
        inverse_name="parent_id",
    )

    @api.model
    def _selection_reference_value(self):
        models = (
            self.env["ir.model"]
            .sudo()
            .search([("transient", "=", False)], order="name asc")
        )
        return [(model.model, model.name) for model in models]

    @api.onchange("value_type")
    def _onchange_value_type(self):
        if self.value_type == "fixed" and self.field_relation:
            record = self.env[self.field_relation].search([], limit=1)
            self.fixed_value = f"{self.field_relation},{record.id}"

    @api.onchange("search_field_id")
    def _onchange_search_field_id(self):
        """Leave the search_subfield_id field empty to avoid inconsistencies."""
        self.search_subfield_id = False

    @api.depends("related_model")
    def _compute_model(self):
        for item in self:
            item.model = (
                item.template_id.model
                if item.related_model == "header"
                else item.template_id.child_model
            )

    def _get_fixed_field_name_ttype_mapped(self):
        return {
            "char": "fixed_value_char",
            "date": "fixed_value_date",
            "datetime": "fixed_value_datetime",
            "float": "fixed_value_float",
            "html": "fixed_value_html",
            "integer": "fixed_value_integer",
            "selection": "fixed_value_selection",
            "text": "fixed_value_text",
            "many2one": "fixed_value",
        }

    def _get_fixed_value(self):
        self.ensure_one()
        f_name = self._get_fixed_field_name_ttype_mapped()[self.field_ttype]
        f_value = self[f_name]
        if self.field_ttype == "selection":
            f_value = f_value.value
        return f_value

    def _replace_text(self, text, letters, prefix):
        for letter in letters:
            text = text.replace(letter, prefix + letter)
            text = text.replace(letter.upper(), prefix + letter.upper())
        return text

    def _process_datetime_value(self, value):
        if self.field_ttype not in ("date", "datetime") or not self.date_format:
            return value
        # We need to replace -short because it is not respected in databases with
        # different capitalization. (example: *d/*m/*Y and *d/*m/*y)
        date_format = self.date_format.replace("*", "%").replace("-short", "")
        if self.field_ttype == "datetime":
            time_format = self.time_format.replace("*", "%")
            date_format += " " + time_format
        datetime_object = datetime.strptime(value, date_format)
        value = datetime_object.strftime("%Y-%m-%d %H:%M:%S")
        return value

    def _process_float_value(self, value):
        if self.field_ttype != "float":
            return value
        separator_mapped = {"dot": ".", "comma": ","}
        if self.thousand_separator and self.thousand_separator != "none":
            value = value.replace(separator_mapped[self.thousand_separator], "")
        if self.decimal_separator:
            value = value.replace(separator_mapped[self.decimal_separator], ".")
        return float(value)

    def _get_record_search_from_value(self, value):
        """This method can be overridden in some use cases if needed."""
        if not self.search_field_id:
            return False
        domain_field_name = self.search_field_name
        if self.search_subfield_id:
            domain_field_name += ".%s" % (self.search_subfield_id.name)
        return self.env[self.field_relation].search(
            [(domain_field_name, "=", value)], limit=1
        )

    def _process_value(self, value):
        # Apply pattern
        if self.pattern:
            new_value = re.findall(self.pattern, value)
            if new_value:
                value = new_value[0]
        # Extra changes (dates or float)
        if self.field_ttype in ("date", "datetime"):
            value = self._process_datetime_value(value)
        elif self.field_ttype == "float":
            value = self._process_float_value(value)
        # Apply mapping (if any is found, we return that)
        mapped_items = self.mapped_ids.filtered(lambda x: x.origin == value)
        if mapped_items:
            return fields.first(mapped_items).value
        # Search and return the record only if found
        if self.search_field_id:
            record = self._get_record_search_from_value(value)
            if record:
                return record
        if self.default_value:
            return self.default_value
        return value

    def _get_field_value(self, text):
        field_value = False
        if self.pattern:
            res = re.findall(self.pattern, text)
            if res:
                field_value = self._process_value(res[0])
        return field_value


class BaseImportPdfTemplateLineMapped(models.Model):
    _name = "base.import.pdf.template.line.mapped"
    _description = "Base Import Pdf Template Line Mapped"
    _order = "value asc, id"

    parent_id = fields.Many2one(
        comodel_name="base.import.pdf.template.line", required=True
    )
    origin = fields.Char()
    value = fields.Reference(
        selection="_selection_reference_value",
    )

    @api.model
    def _selection_reference_value(self):
        models = (
            self.env["ir.model"]
            .sudo()
            .search([("transient", "=", False)], order="name asc")
        )
        return [(model.model, model.name) for model in models]
