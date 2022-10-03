# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class EDIExchangePOGenerate(Component):
    """Generate purchase orders."""

    _name = "edi.output.ubl.purchase.order"
    _inherit = "edi.component.output.mixin"
    _usage = "output.generate.purchase.order"

    def generate(self):
        return self._generate_ubl_xml()

    # TODO: add tests
    def _generate_ubl_xml(self):
        order = self.record
        doc_type = order.get_ubl_purchase_order_doc_type()
        if not doc_type:
            raise NotImplementedError("TODO: handle no doc type")
        version = order.get_ubl_version()
        xml_string = order.generate_ubl_xml_string(doc_type, version=version)
        return xml_string
