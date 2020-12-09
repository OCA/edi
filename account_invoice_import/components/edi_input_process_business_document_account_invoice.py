# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging

from odoo import _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero, float_round

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class EDIInputProcessBusinessDocumentImport(Component):
    _name = "edi.input.process.account.invoice.import"
    _inherit = "edi.input.process.business.document.import"
    _usage = "edi.input.process.account_invoice_import"

    def process(self):
        parsed_inv = json.loads(self.exchange_record._get_file_content())
        parsed_inv = self.env["account.invoice.import"].pre_process_parsed_inv(
            parsed_inv
        )
        import_config = (
            self.backend.account_invoice_import_config_ids.convert_to_import_config()
        )
        if self.exchange_record.record.state in ["update", "update-from-invoice"]:
            invoice = self._update_invoice(parsed_inv, import_config)
        else:
            invoice = self._create_invoice(parsed_inv, import_config)
        self.exchange_record.write({"res_id": invoice.id, "model": invoice._name})

    # Creation invoice methods

    def _create_invoice(self, parsed_inv, import_config):
        aio = self.env["account.move"]
        (vals, import_config) = self._prepare_create_invoice_vals(
            parsed_inv, import_config=import_config
        )
        _logger.debug("Invoice vals for creation: %s", vals)
        invoice = aio.create(vals)
        self._post_process_invoice(parsed_inv, invoice, import_config)
        _logger.info("Invoice ID %d created", invoice.id)
        self._post_create_or_update(parsed_inv, invoice)
        return invoice

    def _prepare_create_invoice_vals(self, parsed_inv, import_config=False):
        assert parsed_inv.get("pre-processed"), "pre-processing not done"
        # WARNING: on future versions, import_config will probably become
        # a required argument
        amo = self.env["account.move"]
        company = (
            self.env["res.company"].browse(self.env.context.get("force_company"))
            or self.env.user.company_id
        )
        if parsed_inv["type"] in ("out_invoice", "out_refund"):
            partner_type = "customer"
        else:
            partner_type = "supplier"
        partner = self._match_partner(
            parsed_inv["partner"], parsed_inv["chatter_msg"], partner_type=partner_type
        )
        partner = partner.commercial_partner_id
        currency = self._match_currency(
            parsed_inv.get("currency"), parsed_inv["chatter_msg"]
        )
        journal_id = (
            amo.with_context(type=parsed_inv["type"], company_id=company.id)
            ._get_default_journal()
            .id
        )
        vals = {
            "partner_id": partner.id,
            "currency_id": currency.id,
            "type": parsed_inv["type"],
            "company_id": company.id,
            "invoice_origin": parsed_inv.get("origin"),
            "invoice_payment_ref": parsed_inv.get("invoice_number"),
            "invoice_date": parsed_inv.get("date"),
            "journal_id": journal_id,
            "invoice_line_ids": [],
        }
        vals = amo.play_onchanges(vals, ["partner_id"])
        # Force due date of the invoice
        if parsed_inv.get("date_due"):
            vals["invoice_date_due"] = parsed_inv.get("date_due")
        # Bank info
        if parsed_inv.get("iban"):
            partner_bank = self._match_partner_bank(
                partner,
                parsed_inv["iban"],
                parsed_inv.get("bic"),
                parsed_inv["chatter_msg"],
                create_if_not_found=company.invoice_import_create_bank_account,
            )
            if partner_bank:
                vals["invoice_partner_bank_id"] = partner_bank.id
        if not import_config:
            if not partner.invoice_import_ids:
                raise UserError(
                    _("Missing Invoice Import Configuration on partner '%s'.")
                    % partner.display_name
                )
            else:
                import_config_obj = partner.invoice_import_ids[0]
                import_config = import_config_obj.convert_to_import_config()
        # get invoice line vals
        vals["invoice_line_ids"] = []
        if import_config["invoice_line_method"].startswith("1line"):
            self._prepare_line_vals_1line(partner, vals, parsed_inv, import_config)
        elif import_config["invoice_line_method"].startswith("nline"):
            self._prepare_line_vals_nline(partner, vals, parsed_inv, import_config)
        # Write analytic account + fix syntax for taxes
        analytic_account = import_config.get("account_analytic", False)
        if analytic_account:
            for line in vals["invoice_line_ids"]:
                line[2]["account_analytic_id"] = analytic_account.id
        return (vals, import_config)

    def _prepare_line_vals_1line(self, partner, vals, parsed_inv, import_config):
        line_model = self.env["account.move.line"]
        if import_config["invoice_line_method"] == "1line_no_product":
            if import_config["taxes"]:
                il_tax_ids = [(6, 0, import_config["taxes"].ids)]
            else:
                il_tax_ids = False
            il_vals = {
                "account_id": import_config["account"].id,
                "tax_ids": il_tax_ids,
                "price_unit": parsed_inv.get("amount_untaxed"),
            }
        elif import_config["invoice_line_method"] == "1line_static_product":
            product = import_config["product"]
            il_vals = {"product_id": product.id, "move_id": vals}
            il_vals = line_model.play_onchanges(il_vals, ["product_id"])
            il_vals.pop("move_id")
        if import_config.get("label"):
            il_vals["name"] = import_config["label"]
        elif parsed_inv.get("description"):
            il_vals["name"] = parsed_inv["description"]
        elif not il_vals.get("name"):
            il_vals["name"] = _("MISSING DESCRIPTION")
        self._set_1line_price_unit_and_quantity(il_vals, parsed_inv)
        self._set_1line_start_end_dates(il_vals, parsed_inv)
        vals["invoice_line_ids"].append((0, 0, il_vals))

    def _prepare_line_vals_nline(self, partner, vals, parsed_inv, import_config):
        line_model = self.env["account.move.line"]
        start_end_dates_installed = hasattr(line_model, "start_date") and hasattr(
            line_model, "end_date"
        )
        if not parsed_inv.get("lines"):
            raise UserError(
                _(
                    "You have selected a Multi Line method for this import "
                    "but Odoo could not extract/read any XML file inside "
                    "the PDF invoice."
                )
            )
        if import_config["invoice_line_method"] == "nline_no_product":
            static_vals = {"account_id": import_config["account"].id}
        elif import_config["invoice_line_method"] == "nline_static_product":
            sproduct = import_config["product"]
            static_vals = {"product_id": sproduct.id, "move_id": vals}
            static_vals = line_model.play_onchanges(static_vals, ["product_id"])
            static_vals.pop("move_id")
        else:
            static_vals = {}
        for line in parsed_inv["lines"]:
            il_vals = static_vals.copy()
            if import_config["invoice_line_method"] == "nline_auto_product":
                product = self._match_product(
                    line["product"], parsed_inv["chatter_msg"], seller=partner
                )
                il_vals = {"product_id": product.id, "move_id": vals}
                il_vals = line_model.play_onchanges(il_vals, ["product_id"])
                il_vals.pop("move_id")
            elif import_config["invoice_line_method"] == "nline_no_product":
                taxes = self._match_taxes(line.get("taxes"), parsed_inv["chatter_msg"])
                il_vals["tax_ids"] = [(6, 0, taxes.ids)]
            if not il_vals.get("account_id") and il_vals.get("product_id"):
                product = self.env["product.product"].browse(il_vals["product_id"])
                raise UserError(
                    _(
                        "Account missing on product '%s' or on it's related "
                        "category '%s'."
                    )
                    % (product.display_name, product.categ_id.display_name)
                )
            if line.get("name"):
                il_vals["name"] = line["name"]
            elif not il_vals.get("name"):
                il_vals["name"] = _("MISSING DESCRIPTION")
            if start_end_dates_installed:
                il_vals["start_date"] = line.get("date_start") or parsed_inv.get(
                    "date_start"
                )
                il_vals["end_date"] = line.get("date_end") or parsed_inv.get("date_end")
            uom = self._match_uom(line.get("uom"), parsed_inv["chatter_msg"])
            il_vals["product_uom_id"] = uom.id
            il_vals.update(
                {
                    "quantity": line["qty"],
                    "price_unit": line["price_unit"],  # TODO fix for tax incl
                }
            )
            vals["invoice_line_ids"].append((0, 0, il_vals))

    def _set_1line_price_unit_and_quantity(self, il_vals, parsed_inv):
        """For the moment, we only take into account the 'price_include'
        option of the first tax"""
        il_vals["quantity"] = 1
        il_vals["price_unit"] = parsed_inv.get("amount_total")
        if il_vals.get("tax_ids"):
            for tax_entry in il_vals["tax_ids"]:
                if tax_entry:
                    tax_id = False
                    if tax_entry[0] == 4:
                        tax_id = tax_entry[1]
                    elif tax_entry[0] == 6:
                        tax_id = tax_entry[2][0]
                    if tax_id:
                        first_tax = self.env["account.tax"].browse(tax_id)
                        if not first_tax.price_include:
                            il_vals["price_unit"] = parsed_inv.get("amount_untaxed")
                            break

    def _set_1line_start_end_dates(self, il_vals, parsed_inv):
        """Only useful if you have installed the module account_cutoff_prepaid
        from https://github.com/OCA/account-closing"""
        ailo = self.env["account.move.line"]
        if (
            parsed_inv.get("date_start")
            and parsed_inv.get("date_end")
            and hasattr(ailo, "start_date")
            and hasattr(ailo, "end_date")
        ):
            il_vals["start_date"] = parsed_inv.get("date_start")
            il_vals["end_date"] = parsed_inv.get("date_end")

    def _prepare_global_adjustment_line(self, diff_amount, invoice, import_config):
        ailo = self.env["account.move.line"]
        prec = invoice.currency_id.rounding
        il_vals = {"name": _("Adjustment"), "quantity": 1, "price_unit": diff_amount}
        # no taxes nor product on such a global adjustment line
        if import_config["invoice_line_method"] in "nline_no_product":
            il_vals["account_id"] = import_config["account"].id
        elif import_config["invoice_line_method"] == "nline_static_product":
            account = ailo.get_invoice_line_account(
                invoice.type,
                import_config["product"],
                invoice.fiscal_position_id,
                invoice.company_id,
            )
            il_vals["account_id"] = account.id
        elif import_config["invoice_line_method"] == "nline_auto_product":
            res_cmp = float_compare(diff_amount, 0, precision_rounding=prec)
            company = invoice.company_id
            if res_cmp > 0:
                if not company.adjustment_debit_account_id:
                    raise UserError(
                        _(
                            "You must configure the 'Adjustment Debit Account' "
                            "on the Accounting Configuration page."
                        )
                    )
                il_vals["account_id"] = company.adjustment_debit_account_id.id
            else:
                if not company.adjustment_credit_account_id:
                    raise UserError(
                        _(
                            "You must configure the 'Adjustment Credit Account' "
                            "on the Accounting Configuration page."
                        )
                    )
                il_vals["account_id"] = company.adjustment_credit_account_id.id
        _logger.debug("Prepared global ajustment invoice line %s", il_vals)
        return il_vals

    def _post_process_invoice(self, parsed_inv, invoice, import_config):
        if parsed_inv.get("type") in ("out_invoice", "out_refund"):
            return
        prec = invoice.currency_id.rounding
        # If untaxed amount is wrong, create adjustment lines
        if (
            import_config["invoice_line_method"].startswith("nline")
            and invoice.invoice_line_ids
            and float_compare(
                parsed_inv["amount_untaxed"],
                invoice.amount_untaxed,
                precision_rounding=prec,
            )
        ):
            # Try to find the line that has a problem
            # TODO : on invoice creation, the lines are in the same
            # order, but not on invoice update...
            for i in range(len(parsed_inv["lines"])):
                if "price_subtotal" not in parsed_inv["lines"][i]:
                    continue
                iline = invoice.invoice_line_ids[i]
                odoo_subtotal = iline.price_subtotal
                parsed_subtotal = parsed_inv["lines"][i]["price_subtotal"]
                if float_compare(
                    odoo_subtotal, parsed_subtotal, precision_rounding=prec
                ):
                    diff_amount = float_round(
                        parsed_subtotal - odoo_subtotal, precision_rounding=prec
                    )
                    _logger.info(
                        "Price subtotal difference found on invoice line %d "
                        "(source:%s, odoo:%s, diff:%s).",
                        i + 1,
                        parsed_subtotal,
                        odoo_subtotal,
                        diff_amount,
                    )
                    copy_dict = {
                        "name": _("Adjustment on %s") % iline.name,
                        "quantity": 1,
                        "price_unit": diff_amount,
                    }
                    if import_config["invoice_line_method"] == "nline_auto_product":
                        copy_dict["product_id"] = False
                    # Add the adjustment line
                    iline.copy(copy_dict)
                    _logger.info("Adjustment invoice line created")
        if float_compare(
            parsed_inv["amount_untaxed"],
            invoice.amount_untaxed,
            precision_rounding=prec,
        ):
            # create global ajustment line
            diff_amount = float_round(
                parsed_inv["amount_untaxed"] - invoice.amount_untaxed,
                precision_rounding=prec,
            )
            _logger.info(
                "Amount untaxed difference found " "(source: %s, odoo:%s, diff:%s)",
                parsed_inv["amount_untaxed"],
                invoice.amount_untaxed,
                diff_amount,
            )
            il_vals = self._prepare_global_adjustment_line(
                diff_amount, invoice, import_config
            )
            il_vals["move_id"] = invoice.id
            self.env["account.move.line"].create(il_vals)
            _logger.info("Global adjustment invoice line created")
        # Invalidate cache
        invoice = self.env["account.move"].browse(invoice.id)
        assert not float_compare(
            parsed_inv["amount_untaxed"],
            invoice.amount_untaxed,
            precision_rounding=prec,
        )
        # Force tax amount if necessary
        if float_compare(
            invoice.amount_total, parsed_inv["amount_total"], precision_rounding=prec
        ):
            raise UserError(
                _(
                    "The total amount is different from the untaxed amount, "
                    "no way to solve this issue right now"
                )
            )

    # Update invoice methods

    def _update_invoice(self, parsed_inv, import_config):
        invoice = self.exchange_record.record.invoice_id
        partner = self._match_partner(
            parsed_inv["partner"], parsed_inv["chatter_msg"], partner_type="supplier"
        )
        partner = partner.commercial_partner_id
        if partner != invoice.commercial_partner_id:
            raise UserError(
                _(
                    "The supplier of the imported invoice (%s) is different from "
                    "the supplier of the invoice to update (%s)."
                )
                % (partner.name, invoice.commercial_partner_id.name)
            )
        currency = self._match_currency(
            parsed_inv.get("currency"), parsed_inv["chatter_msg"]
        )
        if currency != invoice.currency_id:
            raise UserError(
                _(
                    "The currency of the imported invoice (%s) is different from "
                    "the currency of the existing invoice (%s)"
                )
                % (currency.name, invoice.currency_id.name)
            )
        vals = self._prepare_update_invoice_vals(parsed_inv, invoice)
        _logger.debug("Updating supplier invoice with vals=%s", vals)
        invoice.write(vals)
        if (
            parsed_inv.get("lines")
            and import_config["invoice_line_method"] == "nline_auto_product"
        ):
            self._update_invoice_lines(parsed_inv, invoice, partner)
        self._post_process_invoice(parsed_inv, invoice, import_config)
        if import_config["account_analytic"]:
            invoice.invoice_line_ids.write(
                {"account_analytic_id": import_config["account_analytic"].id}
            )
        self._post_create_or_update(parsed_inv, invoice)
        _logger.info(
            "Supplier invoice ID %d updated via import of file %s",
            invoice.id,
            self.exchange_record.record.invoice_filename,
        )
        return invoice

    def _update_invoice_lines(self, parsed_inv, invoice, seller):
        chatter = parsed_inv["chatter_msg"]
        dpo = self.env["decimal.precision"]
        qty_prec = dpo.precision_get("Product Unit of Measure")
        existing_lines = []
        for eline in invoice.invoice_line_ids:
            price_unit = 0.0
            if not float_is_zero(eline.quantity, precision_digits=qty_prec):
                price_unit = eline.price_subtotal / float(eline.quantity)
            existing_lines.append(
                {
                    "product": eline.product_id or False,
                    "name": eline.name,
                    "qty": eline.quantity,
                    "uom": eline.product_uom_id,
                    "line": eline,
                    "price_unit": price_unit,
                }
            )
        compare_res = self._compare_lines(
            existing_lines, parsed_inv["lines"], chatter, seller=seller
        )
        if not compare_res:
            return
        for eline, cdict in list(compare_res["to_update"].items()):
            write_vals = {}
            if cdict.get("qty"):
                chatter.append(
                    _(
                        "The quantity has been updated on the invoice line "
                        "with product '%s' from %s to %s %s"
                    )
                    % (
                        eline.product_id.display_name,
                        cdict["qty"][0],
                        cdict["qty"][1],
                        eline.product_uom_id.name,
                    )
                )
                write_vals["quantity"] = cdict["qty"][1]
            if cdict.get("price_unit"):
                chatter.append(
                    _(
                        "The unit price has been updated on the invoice "
                        "line with product '%s' from %s to %s %s"
                    )
                    % (
                        eline.product_id.display_name,
                        eline.price_unit,
                        cdict["price_unit"][1],  # TODO fix
                        invoice.currency_id.name,
                    )
                )
                write_vals["price_unit"] = cdict["price_unit"][1]
            if write_vals:
                invoice.write({"invoice_line_ids": [(1, eline.id, write_vals)]})
        if compare_res["to_remove"]:
            to_remove_label = [
                "{} {} x {}".format(
                    l.quantity, l.product_uom_id.name, l.product_id.name
                )
                for l in compare_res["to_remove"]
            ]
            chatter.append(
                _("%d invoice line(s) deleted: %s")
                % (len(compare_res["to_remove"]), ", ".join(to_remove_label))
            )
            for eline in compare_res["to_remove"]:
                invoice.write({"invoice_line_ids": [(2, eline.id)]})
        if compare_res["to_add"]:
            to_create_label = []
            for add in compare_res["to_add"]:
                line_vals = self._prepare_create_invoice_line(
                    add["product"], add["uom"], add["import_line"], invoice
                )
                invoice.write({"invoice_line_ids": [(0, 0, line_vals)]})
                new_line = invoice.invoice_line_ids.filtered(
                    lambda r: r.product_id.id == line_vals["product_id"]
                )
                to_create_label.append(
                    "%s %s x %s"
                    % (new_line.quantity, new_line.product_uom_id.name, new_line.name)
                )
            chatter.append(
                _("%d new invoice line(s) created: %s")
                % (len(compare_res["to_add"]), ", ".join(to_create_label))
            )
        return True

    def _prepare_create_invoice_line(self, product, uom, import_line, invoice):
        new_line = self.env["account.move.line"].new(
            {"move_id": invoice, "quantity": import_line["qty"], "product_id": product}
        )
        new_line._onchange_product_id()
        vals = {
            f: new_line._fields[f].convert_to_write(new_line[f], new_line)
            for f in new_line._cache
        }
        vals.update(
            {
                "product_id": product.id,
                "price_unit": import_line.get("price_unit"),
                "quantity": import_line["qty"],
                "product_uom_id": uom.id,
                "move_id": invoice.id,
            }
        )
        return vals

    def _prepare_update_invoice_vals(self, parsed_inv, invoice):
        bdio = self.env["business.document.import"]
        vals = {
            "ref": parsed_inv.get("invoice_number"),
            "invoice_date": parsed_inv.get("date"),
        }
        if parsed_inv.get("date_due"):
            vals["invoice_date_due"] = parsed_inv["date_due"]
        if parsed_inv.get("iban"):
            company = invoice.company_id
            partner_bank = bdio._match_partner_bank(
                invoice.commercial_partner_id,
                parsed_inv["iban"],
                parsed_inv.get("bic"),
                parsed_inv["chatter_msg"],
                create_if_not_found=company.invoice_import_create_bank_account,
            )
            if partner_bank:
                vals["invoice_partner_bank_id"] = partner_bank.id
        return vals
