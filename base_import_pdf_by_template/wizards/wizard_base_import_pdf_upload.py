# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tests import Form

logger = logging.getLogger(__name__)


class WizardBaseImportPdfUpload(models.TransientModel):
    _name = "wizard.base.import.pdf.upload"
    _description = "Wizard Base Import Pdf Upload"

    model = fields.Char()
    record_ref = fields.Reference(selection="_selection_reference_value")
    attachment_ids = fields.Many2many(comodel_name="ir.attachment", string="Files")
    allowed_template_ids = fields.Many2many(
        comodel_name="base.import.pdf.template", compute="_compute_allowed_template_ids"
    )
    data = fields.Text(compute="_compute_data", store=True)
    line_ids = fields.One2many(
        comodel_name="wizard.base.import.pdf.upload.line",
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

    @api.depends("model")
    def _compute_allowed_template_ids(self):
        template_model = self.env["base.import.pdf.template"]
        for item in self:
            item.allowed_template_ids = template_model._get_items_from_model(item.model)

    @api.depends("line_ids")
    def _compute_data(self):
        for item in self:
            data = ""
            for line in item.line_ids:
                data += line.data if line.data else ""
            item.data = data

    def action_process(self):
        """Creamos las lineas, auto-detección + procesar cada línea."""
        if not self.allowed_template_ids:
            raise UserError(_("There is no template that can be applied"))
        lines = []
        for attachment in self.attachment_ids:
            lines.append((0, 0, {"attachment_id": attachment.id}))
        self.line_ids = lines
        # Error si corresponde
        lines_without_template = self.line_ids.filtered(lambda x: not x.template_id)
        if lines_without_template:
            raise UserError(
                _(
                    "No template has been auto-detected from %s, it may be "
                    "necessary to create a new one."
                )
                % fields.first(lines_without_template).attachment_id.name
            )
        # Process + return records
        records = self.env[self.model]
        for line in self.line_ids:
            records += line.action_process()
        action = {
            "type": "ir.actions.act_window",
            "res_model": records._name,
            "context": self.env.context,
        }
        if len(records) == 1:
            action.update(
                {
                    "views": [(False, "form")],
                    "view_mode": "form",
                    "res_id": records.id,
                }
            )
        else:
            action.update(
                {
                    "name": _("Generated Documents"),
                    "views": [(False, "tree"), (False, "form")],
                    "view_mode": "tree,form",
                    "domain": [("id", "in", records.ids)],
                }
            )
        return action


class WizardBaseImportPdfUploadLine(models.TransientModel):
    _name = "wizard.base.import.pdf.upload.line"
    _description = "Wizard Base Import Pdf upload Line"
    _inherit = "wizard.base.import.pdf.mixin"

    parent_id = fields.Many2one(comodel_name="wizard.base.import.pdf.upload")
    data = fields.Text()
    template_id = fields.Many2one(
        comodel_name="base.import.pdf.template",
        string="Template",
        compute="_compute_template_id",
        store=True,
    )
    extraction_mode = fields.Selection(related="template_id.extraction_mode")
    log_text = fields.Html()

    @api.depends("attachment_id")
    def _compute_template_id(self):
        self.template_id = False
        for item in self.filtered("attachment_id"):
            data = item._parse_pdf_grouped()
            text = ""
            for key in list(data.keys()):
                text += "".join(data[key])
            item.template_id = (
                item.parent_id.allowed_template_ids._auto_detect_from_text(text)
            )

    def action_process(self):
        """Parse the file again, this time with the corresponding extraction mode."""
        self.extraction_mode = self.template_id.extraction_mode
        data = self._parse_pdf()
        self.data = "".join(data)
        record = self._process_form()
        self.attachment_id.write({"res_model": record._name, "res_id": record.id})
        return record

    def _add_log_error_text(self, field_name, value):
        text = _("Error to set %(field_name)s with value %(value)s") % {
            "field_name": field_name,
            "value": value,
        }
        self._add_log_text(text)

    def _add_log_text(self, text):
        markup_text = Markup("<p>{text}</p>").format(text=text)
        if not self.log_text:
            self.log_text = markup_text
        else:
            self.log_text += markup_text

    def _process_set_value_form(self, _form, field_name, value):
        old_value = getattr(_form, field_name)
        model_name = self.env.context.get("model_name")
        related_model = self.env.context.get("related_model")
        template_line = self.template_id.line_ids.filtered(
            lambda x: x.model == model_name
            and x.field_name == field_name
            and x.related_model == related_model
        )
        if not template_line:
            return
        if template_line.log_distinct_value:
            if old_value != value:
                old_value_data = (
                    old_value.display_name
                    if isinstance(old_value, models.Model)
                    else old_value
                )
                new_value_data = (
                    value.display_name if isinstance(value, models.Model) else value
                )
                text = _(
                    """%(item_name)s has been set with %(new_value)s instead of
                    %(old_value)s"""
                ) % {
                    "item_name": getattr(_form, "name"),  # noqa: B009
                    "old_value": old_value_data,
                    "new_value": new_value_data,
                }
                self._add_log_text(text)
        else:
            try:
                setattr(_form, field_name, value)
            except Exception:
                self._add_log_error_text(field_name, value)

    def _process_form(self):
        """Create record with Form() according to text."""
        text = self.data
        template = self.template_id
        model = self.env[template.model]
        model = self.parent_id.record_ref or self.env[template.model]
        ctx = template._prepare_ctx_from_model(template.model)
        model_form = Form(model.with_context(**ctx))
        # Set the values of the header in Form
        header_values = template._get_field_header_values(text)
        for field_name in list(header_values.keys()):
            field_data = header_values[field_name]
            self.with_context(
                model_name=template.model, related_model="header"
            )._process_set_value_form(model_form, field_name, field_data)
        # Repeat the process for lines
        table_info = template._get_table_info(text)
        lines_values = template._get_field_child_values(table_info)
        for line in lines_values:
            child_line = getattr(model_form, template.child_field_name)
            with child_line.new() as line_form:
                # Fixed values (it is not possible to set context to lines)
                child_fixed_values = template._get_fixed_fields_from_model(
                    template.child_model
                )
                for field_name in list(child_fixed_values.keys()):
                    child_field_value = child_fixed_values[field_name]
                    try:
                        setattr(line_form, field_name, child_field_value)
                    except Exception:
                        self._add_log_error_text(field_name, child_field_value)
                # et the values of any line
                for field_name in list(line.keys()):
                    self.with_context(
                        model_name=template.child_model, related_model="lines"
                    )._process_set_value_form(line_form, field_name, line[field_name])
        try:
            # Prepare vals (similar to .save()) + apply defaults (in case it has changed
            # in some onchange for example: warehouse_id from sale orders)
            vals = model_form._get_save_values()
            for key in ctx:
                if key.startswith("default_"):
                    field = key.replace("default_", "")
                    if field in vals and not self.parent_id.record_ref:
                        vals.update({field: ctx[key]})
                    elif self.parent_id.record_ref:
                        vals.update({field: ctx[key]})
            # Create or update
            if self.parent_id.record_ref:
                model.with_context(**ctx).write(vals)
                record = self.parent_id.record_ref
            else:
                record = model.with_context(**ctx).create(vals)
        except AssertionError as err:
            raise UserError(err) from err
        if self.log_text:
            record._message_log(body=self.log_text)
        return record
