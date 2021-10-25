# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    if not version:
        return

    # Fix typo coma -> comma
    cr.execute(
        """
        UPDATE res_partner SET simple_pdf_decimal_separator='comma'
        WHERE simple_pdf_decimal_separator='coma'
        """
    )

    cr.execute(
        """
        UPDATE res_partner SET simple_pdf_thousand_separator='comma'
        WHERE simple_pdf_thousand_separator='coma'
        """
    )
