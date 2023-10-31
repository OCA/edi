# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from collections import OrderedDict
from io import BytesIO, TextIOWrapper

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from odoo.addons.base.models.res_partner import _lang_get

logger = logging.getLogger(__name__)


UBL_VERSION = [
    ("2.0", "2.0"),
    ("2.1", "2.1"),
    ("2.2", "2.2"),
]


class WamasDocumentXmlConversionTemplate(models.Model):
    _name = "wamas.document.xml.conversion.template"
    _inherit = "base.ubl"
    _description = "WAMAS Document XML Conversion Template"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    ttype = fields.Selection(
        [
            ("from_xml", "From XML"),
            ("to_xml", "To XML"),
        ],
        "Type",
        required=True,
    )
    from_wamas_document_template_id = fields.Many2one(
        "wamas.document.template",
        "From WAMAS Document Template",
    )
    to_wamas_document_template_id = fields.Many2one(
        "wamas.document.template",
        "To WAMAS Document Template",
    )
    ubl_document_name = fields.Char("UBL Document Name")
    ubl_xml_root_name = fields.Char("UBL XML Root Name")
    ubl_version = fields.Selection(UBL_VERSION, "UBL Version")
    ubl_lang = fields.Selection(_lang_get, string="Language")
    mapping_field_ids = fields.One2many(
        "wamas.document.xml.conversion.field", "template_id", "Mapping Fields"
    )
    from_wamas_element_ids = fields.Many2many(
        "wamas.document.element",
        "wamas_document_element_xml_conversion_rel",
        "convesion_template_id",
        "element_id",
        compute="_compute_from_wamas_element_ids",
        store=True,
    )

    @api.depends("ttype", "from_wamas_document_template_id")
    def _compute_from_wamas_element_ids(self):
        for rec in self:
            from_wamas_element_ids = [(5, 0, 0)]

            if rec.ttype == "to_xml":
                for line in rec.from_wamas_document_template_id.line_ids:
                    from_wamas_element_ids.append((4, line.element_id.id))

            rec.from_wamas_element_ids = from_wamas_element_ids

    @api.onchange("ttype")
    def _onchange_ttype(self):
        self.from_wamas_document_template_id = False
        self.to_wamas_document_template_id = False

    def convert_from_xml_to_wamas_document(self, xml_file):
        self.ensure_one()

        # Get XML info
        xml_root = etree.fromstring(xml_file)

        ns = xml_root.nsmap
        main_xmlns = ns.pop(None)
        ns["main"] = main_xmlns
        root_name = False

        if self.ubl_xml_root_name in main_xmlns:
            document = self.ubl_xml_root_name
            root_name = "main:" + self.ubl_xml_root_name

        if not root_name:
            raise UserError(
                _("Cannot find '%s' in the UBL file." % self.ubl_xml_root_name)
            )

        # Check XML file
        xml_string = etree.tostring(
            xml_root, pretty_print=True, encoding="UTF-8", xml_declaration=True
        )
        version = self._ubl_get_version(xml_root, root_name, ns)
        self._ubl_check_xml_schema(xml_string, document, version=version)

        # Get data from XML
        wamas_tmpl = self.to_wamas_document_template_id

        res = []

        for element_line in wamas_tmpl.line_ids:
            element = element_line.element_id

            if element.freq_xml_path:
                lines = xml_root.iterfind(element.freq_xml_path, namespaces=ns)

                idx = 0
                for _dummy in lines:
                    idx += 1

                    res_element = element.get_values_from_xml(
                        xml_root,
                        ns,
                        convert_type=True,
                        result_type="list_tuple",
                        freq=idx,
                    )

                    if res_element:
                        res.append(res_element)
            else:
                res_element = element.get_values_from_xml(
                    xml_root, ns, convert_type=True, result_type="list_tuple"
                )

                if res_element:
                    res.append(res_element)

        # Generate XML file from the `res` above
        lst_lines = []

        for items in res:
            found_element = wamas_tmpl.get_proper_element_from_items(items)
            if not found_element:
                continue

            str_line = found_element.set_values_to_element(items)
            if str_line:
                lst_lines.append(str_line + "\n")

        return lst_lines

    def convert_from_wamas_document_to_xml(self, file_wamas):
        self.ensure_one()

        if isinstance(file_wamas, bytes):
            file_wamas = TextIOWrapper(BytesIO(file_wamas), "utf-8")

        res_wamas = OrderedDict()

        # Get data from WAMAS Document
        for row in file_wamas:
            found_element = (
                self.from_wamas_document_template_id.get_proper_element_from_row(row)
            )

            if not found_element:
                continue

            values = found_element.get_values_from_element(
                row, convert_type=True, result_type="ordered_dict"
            )

            if found_element.code in res_wamas:
                next_key = next(reversed(res_wamas[found_element.code])) + 1
                res_wamas[found_element.code][next_key] = values
            else:
                res_wamas[found_element.code] = OrderedDict()
                res_wamas[found_element.code][0] = values

        res = self.generate_ubl_xml_string(res_wamas)

        return res

    def generate_ubl_xml_string(self, items, version="2.2"):
        self.ensure_one()

        self.check_input_before_generating_ubl_xml_string()

        lang = self.get_ubl_lang()
        version = self.ubl_version or version

        # Generate XML etree
        xml_root = self.with_context(
            lang=lang
        ).generate_wamas_document_element_xml_etree(items, version=version)

        etree.indent(xml_root, space="	")

        xml_string = etree.tostring(
            xml_root, pretty_print=True, encoding="UTF-8", xml_declaration=True
        )

        # Check generated XML string
        self._ubl_check_xml_schema(xml_string, self.ubl_xml_root_name, version=version)

        logger.debug(
            "The UBL XML file of WAMAS Document Element '%s' generated",
            self.name,
        )
        logger.debug(xml_string.decode("utf-8"))

        return xml_string

    def check_input_before_generating_ubl_xml_string(self):
        self.ensure_one()

        if not self.ubl_document_name:
            raise ValidationError(
                _(
                    "Please input 'UBL Document Name' of the conversion "
                    "'%s' to generate UBL file."
                )
                % self.name
            )

        if not self.ubl_document_name:
            raise ValidationError(
                _(
                    "Please input 'UBL XML Root Name' of the conversion "
                    "'%s' to generate UBL file."
                )
                % self.name
            )

        logger.debug(
            "Starting to generate the UBL XML file of WAMAS Document Element '%s'",
            self.name,
        )

    def _add_item_to_xml_etree(
        self,
        items,
        xml_root,
        ns,
        mapping_field_ids,
        dict_parent_node,
        lst_freq_mapping_field=False,
        idx=0,
    ):
        self.ensure_one()

        for line in mapping_field_ids.sorted(key=lambda r: r.sequence):
            _key = (line.namespace, line.name, idx + 1)

            parent_node = xml_root

            if line.parent_id:
                _key_parent = (line.parent_id.namespace, line.parent_id.name, idx + 1)
                parent_node = dict_parent_node[_key_parent]

            node = line.ubl_add_item(items, parent_node, ns, idx=idx)

            if line.namespace == "cac" or line.has_attribute:
                dict_parent_node[_key] = node

            if line.is_freq_element and line.freq_element_id:
                if lst_freq_mapping_field is False:
                    lst_freq_mapping_field = []

                lst_freq_mapping_field.append(line)

        return True

    def generate_wamas_document_element_xml_etree(self, items, version="2.2"):
        self.ensure_one()

        wdxcf_obj = self.env["wamas.document.xml.conversion.field"]

        nsmap, ns = self._ubl_get_nsmap_namespace(
            self.ubl_document_name, version=version
        )
        xml_root = etree.Element(self.ubl_xml_root_name, nsmap=nsmap)

        dict_parent_node = {}
        lst_freq_mapping_field = []

        mapping_field_ids = self.mapping_field_ids.sorted(key=lambda r: r.sequence)
        self._add_item_to_xml_etree(
            items,
            xml_root,
            ns,
            mapping_field_ids,
            dict_parent_node,
            lst_freq_mapping_field,
        )

        dict_parent_node_2 = {}

        for mapping_line in lst_freq_mapping_field:
            lines = wdxcf_obj.search(
                [("template_id", "=", self.id), ("id", "child_of", mapping_line.id)],
                order="sequence",
            )

            for idx in range(1, len(items[mapping_line.freq_element_id.code])):
                self._add_item_to_xml_etree(
                    items, xml_root, ns, lines, dict_parent_node_2, [], idx
                )

        return xml_root

    def get_ubl_version(self):
        self.ensure_one()
        return self.ubl_version or "2.2"

    def get_ubl_lang(self):
        self.ensure_one()
        return self.ubl_lang or "en_US"

    def _get_default_company(self, company_id=False):
        rc_obj = self.env["res.company"]

        res = False

        if company_id:
            res = rc_obj.browse(company_id)
        else:
            res = self.env.ref("base.main_company")

            ICP = self.env["ir.config_parameter"]
            default_company_id = safe_eval(
                ICP.get_param("wamas_to_xml_default_company_id", 0)
            )

            if default_company_id:
                res = rc_obj.browse(default_company_id)

        return res
