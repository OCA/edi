# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class ApplicationSendAcknowledgement(Component):
    """Generate GS1 applicationSendAcknowledgement.
    """

    _name = "gs1.output.applicationSendAcknowledgement"
    _inherit = "edi.gs1.output.mixin"
    _usage = "gs1.out.ApplicationSendAcknowledgement"
    _xsd_schema_path = "static/schemas/gs1/ecom/ApplicationReceiptAcknowledgement.xsd"
