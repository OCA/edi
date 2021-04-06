# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import mimetypes
from datetime import datetime

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "voxel.mixin"]

    voxel_enabled = fields.Boolean(related="company_id.voxel_enabled", readonly=True)
    voxel_job_ids = fields.Many2many(
        comodel_name="queue.job",
        relation="sale_order_voxel_job_rel",
        column1="order_id",
        column2="voxel_job_id",
        string="Jobs",
        copy=False,
    )

    def get_voxel_login(self, company):
        """This method overwrites the one defined in voxel.mixin to provide
        the login for this specific model (sale.order) and company passed as
        parameter
        """
        return company.voxel_sale_order_login_id

    def import_orders_cron(self):
        """Using the method defined in 'voxel.mixin' class for importing
        documents from Voxel"""
        for company in self.env["res.company"].search([]):
            if company.voxel_enabled and self.get_voxel_login(company):
                self.enqueue_import_voxel_documents(company)

    # Voxel import auxiliary methods
    @api.model
    def create_document_from_xml(self, xml_content, voxel_filename, company):
        """This method overwrites the one defined in voxel.mixin to provide
        the mechanism to import a document for this specific model (sale.order)
        """
        error_msgs = []
        order = self._parse_voxel_order(
            xml_content, voxel_filename, error_msgs, company
        )
        # Add internal note to the created sale order
        create_msg = _(
            "Created automatically via voxel import (%s)." % (voxel_filename)
        )
        if error_msgs:
            str_error_msgs = ""
            for error_msg in error_msgs:
                str_error_msgs += "<li>%s</li>" % (error_msg)
            create_msg += _(
                "<br/><span style='font-weight: bold;'>"
                "The following errors were found:</span><br/>"
                "<ul>%s</ul>" % (str_error_msgs)
            )
        order.message_post(body=create_msg)
        return order

    @api.model
    def _parse_voxel_order(self, order_file, order_filename, error_msgs, company):
        filetype = mimetypes.guess_type(order_filename)[0]
        _logger.debug("Order file mimetype: %s", filetype)
        if filetype in ["application/xml", "text/xml"]:
            try:
                xml_root = etree.fromstring(order_file)
            except Exception:
                raise UserError(_("This XML file is not XML-compliant"))
        else:
            raise UserError(_("'%s' is not recognised as an XML file") % order_filename)
        _logger.debug("Starting to import:%s" % (order_filename))
        return self._parse_xml_order(xml_root, error_msgs, company)

    def _parse_xml_order(self, xml_root, error_msgs, company):
        vals = {"company_id": company.id}
        self._parse_general_data_voxel(vals, xml_root, error_msgs)
        self._parse_client_data_voxel(vals, xml_root, error_msgs)
        self._parse_customers_data_voxel(vals, xml_root, error_msgs)
        self._parse_comments_data_voxel(vals, xml_root, error_msgs)
        order = self.create(vals)
        self._parse_product_list_data_voxel(order, xml_root, error_msgs)
        return order

    def _parse_general_data_voxel(self, vals, xml_root, error_msgs):
        general_elements = xml_root.xpath("//GeneralData")
        if general_elements:
            general_data = general_elements[0].attrib
            vals.update(client_order_ref=general_data.get("Ref"))
            # get pricelist
            currency_name = general_data.get("Currency")
            pricelist = self.env["product.pricelist"].search(
                [("currency_id.name", "=", currency_name.upper())], limit=1
            )
            vals.update(pricelist_id=pricelist.id)
            # add date_order
            date_order = general_data.get("Date")
            if date_order:
                vals.update(
                    date_order=datetime.strptime(date_order, "%Y-%m-%dT%H:%M:%S"),
                )
            # add requested_date
            begin_date = general_data.get("BeginDate")
            if begin_date:
                date_format = "%Y-%m-%d"
                # Add time to datetime
                begin_time = general_data.get("BeginTime")
                if begin_time:
                    begin_date += begin_time
                    date_format += "%H:%M:%S"
                vals.update(
                    commitment_date=datetime.strptime(begin_date, date_format),
                    date_order=datetime.strptime(begin_date, date_format),
                )
            # add validity_date
            end_date = general_data.get("EndDate")
            if end_date:
                # add validity_date
                vals.update(
                    validity_date=datetime.strptime(end_date, "%Y-%m-%d").date()
                )

    def _parse_supplier_data_voxel(self, vals, xml_root, error_msgs):
        """Not in use right now."""
        supplier_elements = xml_root.xpath("//Supplier")
        if supplier_elements:
            supplier_data = supplier_elements[0].attrib
            partner_data = self._get_partner_data_voxel(supplier_data)
            partner_data.update(ref=supplier_data.get("SupplierID"))
            partner = self._parse_partner_data_voxel(partner_data)
            company = self.env["res.company"]
            if partner:
                company = self.env["res.company"].search(
                    [("partner_id", "=", partner.id)]
                )
            # Update company_id value
            if company:
                vals.update(company_id=company.id)
            else:
                # Add error message to error_msgs list
                msg_fields = self._get_voxel_msg_fields("res.partner", partner_data)
                error_msgs.append(
                    _(
                        "Couldn't find any <b>Company</b> corresponding to "
                        "the following information extracted from the Voxel "
                        "document:<br/>"
                        "<ul>%s</ul>"
                    )
                    % (msg_fields)
                )

    def _parse_client_data_voxel(self, vals, xml_root, error_msgs):
        client_elements = xml_root.xpath("//Client")
        if client_elements:
            client_data = client_elements[0].attrib
            partner_data = self._get_partner_data_voxel(client_data)
            if not any(partner_data.values()):
                # If there aren't any client data, try to add the first
                # customer as a client (`partner_id`)
                customer_elements = xml_root.xpath("//Customers/Customer")
                if customer_elements:
                    client_data = customer_elements[0].attrib
                    partner_data = self._get_partner_data_voxel(client_data)
                    partner_data.update(name=client_data.get("Customer"))
            if client_data.get("SupplierClientID"):
                partner_data["ref"] = client_data.get("SupplierClientID")
            else:
                partner_data["ref"] = client_data.get("CustomerID")
            partner = self._parse_partner_data_voxel(partner_data)
            if partner:
                vals.update(partner_id=partner.id)

    def _parse_customers_data_voxel(self, vals, xml_root, error_msgs):
        customer_elements = xml_root.xpath("//Customers/Customer")
        if customer_elements:
            customer_data = customer_elements[0].attrib
            partner_data = self._get_partner_data_voxel(customer_data)
            partner_data.update(name=customer_data.get("Customer"))
            if customer_data.get("SupplierClientID"):
                partner_data["ref"] = customer_data.get("SupplierClientID")
            else:
                partner_data["ref"] = customer_data.get("CustomerID")
            partner = self._parse_partner_data_voxel(partner_data)
            # Update partner_shipping_id value
            if partner:
                vals.update(partner_shipping_id=partner.id)
            else:
                # Add error message to error_msgs list
                msg_fields = self._get_voxel_msg_fields("res.partner", partner_data)
                error_msgs.append(
                    _(
                        "Couldn't find any <b>Delivery Address</b> "
                        "corresponding to the following information extracted "
                        "from the Voxel document:<br/>"
                        "<ul>%s</ul>"
                    )
                    % (msg_fields)
                )

    def _parse_partner_data_voxel(self, data, raise_error=True):
        domains = []
        # fill domains list
        if data.get("ref"):
            domains.append([("ref", "=", data.get("ref"))])
        partner = self.env["res.partner"].search(expression.AND(domains))
        if len(partner) == 1:
            return partner
        elif len(partner) == 0:
            domains = []
        # If there are ZERO or more than ONE objects, continue filling domains
        if data.get("country_id"):
            domains.append([("country_id.code_alpha3", "=", data["country_id"])])
        if data.get("state_id"):
            domains.append([("state_id.name", "=", data["state_id"])])
        if data.get("name"):
            domains.append([("name", "=", data["name"])])
        if data.get("email"):
            domains.append([("email", "=", data["email"])])
        if data.get("zip"):
            domains.append([("zip", "=", data["zip"])])
        elif data.get("city"):
            domains.append([("city", "=", data["city"])])
        partner = self.env["res.partner"].search(expression.AND(domains))
        if len(partner) == 1:
            return partner  # return the unique partner matching
        if raise_error:
            raise UserError(
                _("Can't find a suitable partner for this data:\n\n%s" "\nResults: %s")
                % (data, len(partner))
            )
        return self.env["res.partner"]

    def _parse_comments_data_voxel(self, vals, xml_root, error_msgs):
        comments = []
        comment_elements = xml_root.xpath("//Comments/Comment")
        for comment_element in comment_elements:
            comment_data = comment_element.attrib
            subject = comment_data.get("Subject")
            msg = comment_data.get("Msg")
            comments.append(":\n".join(filter(None, [subject, msg])))
        if comments:
            vals.update(note="\n\n".join(comments))

    def _parse_product_list_data_voxel(self, order, xml_root, error_msgs):
        line_elements = xml_root.xpath("//ProductList/Product")
        so_line_obj = self.env["sale.order.line"]
        for line_element in line_elements:
            line_vals = {"order_id": order.id}
            self._parse_product_voxel(line_vals, line_element)
            self._parse_qty_uom_voxel(line_vals, line_element)
            line_vals = so_line_obj.play_onchanges(line_vals, list(line_vals)[1:])
            self._parse_discounts_product_voxel(line_vals, line_element, error_msgs)
            self._parse_taxes_product_voxel(line_vals, line_element, error_msgs)
            if line_vals:
                so_line_obj.create(line_vals)

    def _parse_product_voxel(self, line_vals, line_element):
        product_data = line_element.attrib
        supplier_sku = product_data.get("SupplierSKU")
        item = product_data.get("Item")
        domains = []
        product = self.env["res.partner"]
        if supplier_sku:
            domains.append([("default_code", "=", supplier_sku)])
            product = self.env["product.product"].search(domains[0])
        if len(product) != 1:
            if item:
                domains.append([("name", "=", item)])
            domain = expression.AND(domains)
            if domain:
                product = self.env["product.product"].search(domain)
        if len(product) != 1:
            raise UserError(
                _("Can't find a suitable product for this data:\n\n%s" "\nResults: %s")
                % (product_data, len(product))
            )
        line_vals.update(product_id=product.id)

    def _parse_qty_uom_voxel(self, line_vals, line_element):
        product_data = line_element.attrib
        qty = float(product_data.get("Qty", "1"))
        mu = product_data.get("MU")
        product_uom = self.env["uom.uom"].search([("voxel_code", "=", mu)])
        if len(product_uom) != 1:
            raise UserError(
                _(
                    "Can't find a suitable Unit of Measure for this data:\n\n%s"
                    "\nResults: %s"
                )
                % (product_data, len(product_uom))
            )
        line_vals.update(product_uom_qty=qty, product_uom=product_uom.id)

    def _parse_discounts_product_voxel(self, line_vals, line_element, error_msg):
        discount_line_elements = line_element.xpath("/Discounts/Discount")
        if discount_line_elements:
            discount = discount_line_elements[0].attrib.get("Rate")
            if discount:
                line_vals.update(discount=discount)

    def _parse_taxes_product_voxel(self, line_vals, line_element, error_msgs):
        tax_line_elements = line_element.xpath("/Taxes/Tax")
        for tax_line_element in tax_line_elements:
            tax_line_data = tax_line_element.attrib
            voxel_tax_code = tax_line_data["Type"]
            amount = tax_line_data["Rate"]
            # set domain
            domains = []
            if voxel_tax_code:
                domains.append([("voxel_tax_code", "=", voxel_tax_code)])
            if amount:
                domains.append([("amount", "=", amount)])
            # find tax
            domain = expression.AND(domains)
            tax = self.env["account.tax"].search(domain, limit=1)
            if tax:
                line_vals.setdefault("tax_id", []).append((4, 0, tax.id))
            else:
                # Add error message to error_msgs list
                tax_data = {"voxel_tax_code": voxel_tax_code, "amount": amount}
                msg_fields = self._get_voxel_msg_fields("account.tax", tax_data)
                error_msgs.append(
                    _(
                        "Couldn't find any <b>Tax</b> corresponding to "
                        "the following information extracted from the Voxel "
                        "document:<br/>"
                        "<ul>%s</ul>"
                    )
                    % (msg_fields)
                )

    def _get_partner_data_voxel(self, data):
        return {
            "name": data.get("Company"),
            "email": data.get("Email"),
            "city": data.get("City"),
            "zip": data.get("PC"),
            "state_id": data.get("Province"),
            "country_id": data.get("Country"),
        }

    def _get_voxel_msg_fields(self, model_name, partner_data):
        model = self.env[model_name]
        msg_fields = ""
        for key, value in partner_data.items():
            if partner_data.get(key):
                field_str = model._fields[key].get_description(self.env)["string"]
                msg_fields += "<li>{}: {}</li>".format(field_str, value)
        return msg_fields
