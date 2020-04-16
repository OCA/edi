# -*- coding: utf-8 -*-
# © 2020 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from collections import defaultdict, OrderedDict

from lxml import etree
from openerp import _, api, fields, models
from openerp.exceptions import Warning as UserError

logger = logging.getLogger(__name__)


class InventoryUblImport(models.TransientModel):
    _name = "inventory.ubl.import"
    _inherit = "base.ubl"

    _description = "Inventory Report for UBL file importation"

    document = fields.Binary(
        string="Document to import",
        required=True,
        help="Upload xml file that you received from your supplier.",
    )
    filename = fields.Char()

    @api.multi
    def process_document(self):
        self.ensure_one()
        xml_string = self.document.decode("base64")
        self.env["base.ubl"]._ubl_check_xml_schema(
            xml_string, "InventoryReport", version="2.1"
        )
        try:
            xml_root = etree.fromstring(xml_string)
        except etree.LxmlError as e:
            logger.exception("File is not XML-compliant %s" % e)
            raise UserError(_("This XML file is not XML-compliant"))
        if logger.isEnabledFor(logging.DEBUG):
            pretty_xml_string = etree.tostring(
                xml_root, pretty_print=True, encoding="UTF-8", xml_declaration=True,
            )
            logger.debug("Starting to import the following XML file:")
            logger.debug(pretty_xml_string)
        parsed_document = self.parse_xml_document(xml_root)
        feedback = self.process_data(parsed_document)
        self.store_document(feedback)
        self._process_feedback(feedback)
        return self.redirect_action(feedback)

    @api.model
    def parse_xml_document(self, xml_root):
        start_tag = "{urn:oasis:names:specification:ubl:schema:xsd:"
        if xml_root.tag != start_tag + "InventoryReport-2}InventoryReport":
            raise UserError(_("Please check your file. It seems invalid"))
        ns = xml_root.nsmap
        ns["main"] = ns.pop(None)
        root = "/main:InventoryReport"
        date_xpath = xml_root.xpath(
            "%s/cac:InventoryPeriod/cbc:StartDate" % root, namespaces=ns
        )
        supplier_xpath = xml_root.xpath(
            "%s/cac:InventoryReportingParty" % root, namespaces=ns
        )
        # supplier Cardinality:minOccurs="1" maxOccurs="1"
        supplier_dict = self.ubl_parse_party(supplier_xpath[0], ns)
        customer_xpath = xml_root.xpath(
            "%s/cac:RetailerCustomerParty/cac:Party" % root, namespaces=ns
        )
        # customer Cardinality:minOccurs="1" maxOccurs="1"
        customer_dict = self.ubl_parse_party(customer_xpath[0], ns)
        lines_xpath = xml_root.xpath("%s/cac:InventoryReportLine" % root, namespaces=ns)
        res_lines = []
        for line in lines_xpath:
            res_lines.append(self._ubl_parse_inventory_line(line, ns))
        return {
            "customer": customer_dict,
            "supplier": supplier_dict,
            "date": len(date_xpath) and date_xpath[0].text,
            "product_lines": res_lines,
        }

    def _ubl_parse_inventory_line(self, line_node, ns):
        stock_xph = line_node.xpath("cbc:Quantity", namespaces=ns)
        buyer_id_xph = line_node.xpath(
            "cac:Item/cac:BuyersItemIdentification/cbc:ID", namespaces=ns
        )
        seller_id_xph = line_node.xpath(
            "cac:Item/cac:SellersItemIdentification/cbc:ID", namespaces=ns
        )
        std_id_xph = line_node.xpath(
            "cac:Item/cac:StandardItemIdentification/cbc:ID", namespaces=ns
        )
        return {
            "stock": stock_xph and stock_xph[0].text or False,
            "def_code": buyer_id_xph and buyer_id_xph[0].text or False,
            "sup_code": seller_id_xph and seller_id_xph[0].text or False,
            "barcode": std_id_xph and std_id_xph[0].text or False,
        }

    @api.model
    def process_data(self, parsed_document):
        """ Tasks:
            - guess supplier/seller
            - guess customer/buyer for multicompany context (not implemented in v8)
            - retrieve relative data with product.supplierinfo and product.product
            - write stock by on supplierinfo and/or product.product
        """
        logger.debug(parsed_document)
        feedback = {}
        supplier = self.env["business.document.import"]._match_partner(
            parsed_document.get("supplier"), []
        )
        feedback["supplier"] = supplier.id  # check exists is done above
        prd_lines = parsed_document.get("product_lines")
        inventory_date = parsed_document.get("date")

        # extract stock from provided data in file
        def _populate_stock_by_code(prd_lines, key):
            return {x[key]: float(x["stock"]) for x in prd_lines if x[key]}

        # example {'sup_code': {'UN': 7.0, 'MYCD': 15.0, 'BIN4U': 10.0}, }
        stock_by = OrderedDict()
        for key in ("def_code", "sup_code", "barcode"):
            res = _populate_stock_by_code(prd_lines, key)
            if res:
                stock_by[key] = res
        if not stock_by:
            raise UserError(_("No valid product reference int this file"))
        # query matching query in erp
        sql_result = self._get_supplier_product_data_with_query(supplier, stock_by)
        if not sql_result:
            codes = (
                ("%s" % stock_by)
                .replace("sup_code", _("supplier code"))
                .replace("def_code", _("Internal Reference"))
            )
            raise UserError(
                _(
                    "No matching product for this file '%(file)s'\n"
                    "Check if you have product relations with "
                    "this supplier '%(supp)s' "
                    "(procurement tab in product screen)\n\n"
                    "Here is product refs in the file\n%(codes)s"
                    % {"file": self.filename, "supp": supplier.name, "codes": codes}
                )
            )
        feedback["productinfo"] = self._extract_data_and_update_product(
            sql_result, stock_by, supplier, inventory_date
        )
        feedback["supplierinfo"] = self._extract_data_and_update_supplierinfo(
            sql_result, stock_by, supplier, inventory_date
        )
        if "sup_code" in stock_by:
            unmatch = sorted(self._get_unknown_supplier_codes(supplier, stock_by))
            feedback["unmatch_codes"] = unmatch
        return feedback

    def _get_supplier_product_data_with_query(self, supplier, stock_by):
        """ supplier: record
            stock_by: dict, example:
                {'sup_code': {'BLA': 7.0, 'MYCD': 15.0},
                 'def_code': {'CD': 15.0, 'BRA': 7.0}
                 'bardode': {...} }
        """
        sql_field_names = {
            "def_code": "pp.default_code",
            "sup_code": "ps.product_code",
            "barcode": "pp.ean13",
        }
        query = """
        SELECT ps.id AS supinfo_id, pp.id AS prd_id, ps.product_tmpl_id AS tmpl_id,
               ps.product_code AS sup_code, pp.default_code AS def_code,
               pp.ean13 AS barcode
        FROM product_supplierinfo ps
            LEFT JOIN product_template pt ON pt.id = ps.product_tmpl_id
                LEFT JOIN product_product pp ON pt.id = pp.product_tmpl_id
        WHERE ps.name = %(supplier)s AND (
            %(OR)s
            ) AND pt.active = 't' AND pp.active ='t'
        ORDER BY ps.product_tmpl_id, pp.default_code DESC
        """ % {
            "supplier": "%s",
            # OR count depends of stock_by count
            "OR": " OR ".join(["%s in %%s" % sql_field_names[x] for x in stock_by]),
        }
        params = [tuple(val.keys()) for key, val in stock_by.items() if val]
        params.insert(0, supplier.id)  # first param is supplier
        self.env.cr.execute(query, tuple(params))
        logger.debug(self.env.cr.query)
        logger.debug(params)
        return self.env.cr.dictfetchall()

    def _extract_data_and_update_product(
        self, data, stock_by, supplier, inventory_date
    ):
        """
        Common docstrings to both _extract_data_...() method

        stock_by: dict, example:
            OrderedDict([
                ('def_code', {'NA': 7.0, 'BINALL': 10.0, 'CD': 15.0}),
                ('sup_code', {'UN': 7.0, MYCD': 15.0, 'IPOPO': 17.0, 'BIN4U': 10.0}),
                ('barcode', ...)])

        data example:   result ordered by tmpl_id               |   fields stock
        supinfo_id  prd_id  tmpl_id  sup_code  def_code  barcode| on product.product:
        217         17      13       IPOPO     A6679      ...   | must not be updated
        217         16      13       IPOPO     A6678      ...   | must not be updated
        221         41      37       MYCD2     CD         ...   | must be updated
        220         41      37       MYCD      CD         ...   | must be updated
        219         109     105      BIN4U     BINALL     ...   | must be updated
        254         ...     154      TTTT      YYYY       ...

        On product.supplierinfo:
            - update when stock_by['sup_code'] match with sup_code column
        On product.product:
            - update when stock_by['def_code'] match with def_code column:
              OK for `CD` and `BINALL` (same behavior for barcode column)
            - do NOT update in the case of IPOPO because it has 2 variants
              for the same reference

        We can't guess if IPOPO has many variants by tmpl_id the first time
        the line appear: we need to collect by tmpl_id and process later
        """
        raw_prd_by_tmpl = defaultdict(list)  # relation with product and template
        prd_by_def_code = defaultdict(list)  #
        prd_by_barcode = defaultdict(list)

        def _ckeck_key_in_stock_by(key):
            return row.get(key) and key in stock_by and row[key] in stock_by[key]

        # collect cardinality between product_tmpl_id and product_id
        for row in data:
            # dict below contains duplicates because of the sql cardinality
            # they'll be removed later with set()
            if _ckeck_key_in_stock_by("def_code"):
                prd_by_def_code[row["def_code"]].append(row["prd_id"])
            if _ckeck_key_in_stock_by("barcode"):
                prd_by_barcode[row["prd_by_barcode"]].append(row["prd_id"])
            raw_prd_by_tmpl[row["tmpl_id"]].append(row["prd_id"])
        prd2update = []
        prd_by_tmpl = defaultdict(set)
        for tmplid in raw_prd_by_tmpl:
            # here raw_prd_by_tmpl contains duplicates prd_id entries: (i.e. CD)
            prd_by_tmpl[tmplid] = set(raw_prd_by_tmpl[tmplid])
            if len(prd_by_tmpl[tmplid]) == 1:
                # when matching one for one, it implies to update product.product
                # MYCD/MYCD2 are in this case but not IPOPO
                prd2update.append(prd_by_tmpl[tmplid].pop())
        stk_by_product = {}
        for row in data:
            if not stk_by_product.get(row["prd_id"]) and (
                row["def_code"] or row["sup_code"] or row["barcode"]
            ):
                stk_by_product[row["prd_id"]] = (
                    stock_by["def_code"].get(row["def_code"])
                    or stock_by["sup_code"].get(row["sup_code"])
                    or stock_by["barcode"].get(row["barcode"])
                    or False
                )
        product_ids = []
        # Update products
        for def_code in prd_by_def_code:
            products = self.env["product.product"].browse(
                [
                    x
                    for x in set(prd_by_def_code[def_code])
                    if x in prd2update and x in stk_by_product
                    # ids in prd2update have 1 product by product_tmpl
                ]
            )
            products._update_supplier_stock_from_ubl_inventory(
                supplier, stk_by_product, inventory_date
            )
            product_ids.extend(products.ids)
        return product_ids

    def _extract_data_and_update_supplierinfo(
        self, data, stock_by, supplier, inventory_date
    ):
        """ see _extract_data_and_update_product() docstring
        """
        sinfo_by_sup_code = defaultdict(list)
        stock_by_tmpl = {}
        for row in data:
            # dict below contains duplicates because of the sql cardinality
            # they'll be removed later with set()
            if (
                row.get("sup_code")
                and "sup_code" in stock_by
                and row["sup_code"] in stock_by["sup_code"]
            ):
                stock_by_tmpl[row["tmpl_id"]] = stock_by["sup_code"].get(
                    row["sup_code"]
                )
            sinfo_by_sup_code[row["sup_code"]].append(row["supinfo_id"])
        stk_by_product = {}
        for row in data:
            if not stk_by_product.get(row["prd_id"]) and (
                row["def_code"] or row["sup_code"] or row["barcode"]
            ):
                stk_by_product[row["prd_id"]] = (
                    stock_by["def_code"].get(row["def_code"])
                    or stock_by["sup_code"].get(row["sup_code"])
                    or stock_by["barcode"].get(row["barcode"])
                    or False
                )
        # extract implied writed ids of records
        supplierinfo_ids = []
        for x, ids in sinfo_by_sup_code.items():
            supplierinfo_ids.extend(ids)
        # Update Supplierinfo
        for sup_code in sinfo_by_sup_code:
            # need to make unique ids
            prd_suppinfos = self.env["product.supplierinfo"].browse(
                set(sinfo_by_sup_code[sup_code])
            )
            prd_suppinfos._update_supplier_stock_from_ubl_inventory(
                supplier, stock_by_tmpl, inventory_date
            )
        return list(set(supplierinfo_ids))

    def _get_unknown_supplier_codes(self, supplier, stock_by):
        """ Some products may not have been found in Odoo
            We must provides on relative codes
        """
        # example {'sup_code': {'UN': 7.0, 'MYCD': 15.0, 'BIN4U': 10.0}, }
        codes = list(set(stock_by["sup_code"].keys()))
        domain = [
            ("name", "=", supplier.id),
            ("product_code", "in", codes),
        ]
        erp_supplier_codes = (
            self.env["product.supplierinfo"].search(domain).mapped("product_code")
        )
        return list(set(codes) - set(erp_supplier_codes))

    def _process_feedback(self, feedback):
        """ Process here are generics: you may behavior by
            customizing set_feedback_records() method
        """
        records = self.set_feedback_records(feedback)
        if feedback.get("unmatch_codes"):
            records["unmatch_codes"].message_post(
                _(
                    "These product codes %s have no matching code in ERP"
                    % feedback["unmatch_codes"]
                )
            )

    def set_feedback_records(self, feedback):
        """ Inherit to provide feedback to concerned users
            with the mean you choose
        """
        return {
            "unmatch_codes": self.env["res.partner"].browse(feedback["supplier"]),
        }

    def redirect_action(self, feedback):
        supplier = self.env["res.partner"].browse(feedback["supplier"])
        action = {
            "view_mode": "tree",
            "type": "ir.actions.act_window",
        }
        if feedback.get("supplierinfo"):
            action.update(
                {
                    "name": _("Updated '%s' vendor stock" % supplier.name),
                    "domain": "[('id', 'in', %s)]" % feedback["supplierinfo"],
                    "res_model": "product.supplierinfo",
                    "view_id": self.env.ref(
                        "supplier_inventory_import_ubl.ubl_supinfo_tree_view"
                    ).id,
                }
            )
        elif feedback.get("productinfo"):
            # Used if your file doesn't contains supplier codes
            action.update(
                {
                    "name": _("Updated '%s' vendor stock on product" % supplier.name),
                    "domain": "[('id', 'in', %s)]" % feedback["productinfo"],
                    "res_model": "product.product",
                    "search": False,
                    "view_id": self.env.ref("product.product_product_tree_view").id,
                }
            )
        return action

    def prepare_attachment(self, feedback):
        return {
            "name": self.filename,
            "datas_fname": self.filename,
            "datas": self.document,
            "file_type": "binary",
        }

    def store_document(self, feedback):
        if self.env.user.company_id.inventory_ubl_store_document:
            vals = self.prepare_attachment(feedback)
            supplier = self.env["res.partner"].browse(feedback.get("supplier"))
            if supplier and self.env.user.company_id.inventory_ubl_link_document:
                vals.update({"res_model": supplier._name, "res_id": supplier.id})
            return self.env["ir.attachment"].create(vals)
        return False
