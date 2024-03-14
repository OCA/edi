# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _

from odoo.addons.component.core import Component


class EDIExchangeProductInput(Component):
    """Process products."""

    _name = "edi.input.product.process"
    _inherit = "edi.component.input.mixin"
    _usage = "input.process.product"

    def __init__(self, work_context):
        super().__init__(work_context)
        self.settings = self.type_settings.get("product_import", {})

    def process(self):
        wiz = self._setup_wizard()
        wiz.import_button()
        return _("Products created")

    def _setup_wizard(self):
        """Init a `product.import` instance for current record."""
        ctx = self.settings.get("wiz_ctx", {})
        wiz = self.env["product.import"].with_context(**ctx).sudo().create({})
        wiz.product_file = self.exchange_record._get_file_content(binary=False)
        wiz.product_filename = self.exchange_record.exchange_filename
        wiz.product_file_change()
        return wiz
