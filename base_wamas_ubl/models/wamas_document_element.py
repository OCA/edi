# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import OrderedDict

from odoo import fields, models


def get_item_from_xml(
    recordset_field, xml_root, ns, res, convert_type=False, freq=False
):
    for field in recordset_field:
        xml_path = field.xml_path
        xml_default_value = field.xml_default_value
        xml_default_func = field.xml_default_func

        if field._name == "wamas.document.default.field.template.line":
            field = field.df_field_id

        if xml_path:
            if freq and "%s" in xml_path:
                xml_path = xml_path % str(freq)
            val = xml_root.xpath(xml_path, namespaces=ns)
            if isinstance(val, list):
                val = len(val) > 0 and val[0] or ""
        elif xml_default_value:
            val = xml_default_value
        elif xml_default_func:
            val = str(getattr(field, xml_default_func)())
        else:
            val = ""

        if convert_type and val:
            val = field.get_value_from_string(val)

        if isinstance(res, OrderedDict):
            res[field.code] = val
        elif isinstance(res, list):
            res.append((field.code, val))

    return res


class WamasDocumentElement(models.Model):
    _inherit = "wamas.document.element"

    freq_xml_path = fields.Text("Frequency XML Path", help="It is the relative path")

    def get_values_from_xml(
        self, xml_root, ns, convert_type=False, result_type="ordered_dict", freq=False
    ):
        self.ensure_one()

        res = False

        if result_type == "list_tuple":
            res = []
        elif result_type == "ordered_dict":
            res = OrderedDict()

        # Get value from `row` for `default fields`
        sorted_fields = self.df_field_template_id.line_ids.sorted(
            key=lambda r: r.sequence
        )
        res = get_item_from_xml(
            sorted_fields, xml_root, ns, res, convert_type=convert_type, freq=freq
        )

        # Get value from `row` for `fields`
        sorted_fields = self.field_ids.sorted(key=lambda r: r.sequence)
        res = get_item_from_xml(
            sorted_fields, xml_root, ns, res, convert_type=convert_type, freq=freq
        )

        return res
