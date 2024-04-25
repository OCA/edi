# Copyright 2022 Camptocamp SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo.tests.common import TransactionCase
from odoo.tools import pycompat

from ..utils import xml_purge_nswrapper

ORDER_RESP_WRAPPER_TMPL = """
<OrderResponse
    xmlns="urn:oasis:names:specification:ubl:schema:xsd:OrderResponse-2"
    xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
>
    <cbc:UBLVersionID>2.2</cbc:UBLVersionID>
{}
</OrderResponse>
"""

XML1 = """
    <nswrapper xmlns:foo="http://www.unece.org/cefact/Foo">
        <foo:LovelyNamespacedElement />
    </nswrapper>
"""

XML2 = """
    <nswrapper
            xmlns="urn:oasis:names:specification:ubl:schema:xsd:OrderResponse-2"
            xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
            xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
        >
        <cac:Party>
            <cbc:EndpointID>7302347231111</cbc:EndpointID>
            <cac:PartyIdentification>
                <cbc:ID>7300070011115</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyName>
                <cbc:Name>Moderna Produkter AB</cbc:Name>
            </cac:PartyName>
        </cac:Party>
    </nswrapper>
"""


class TestNSWrapper(TransactionCase):
    maxDiff = None

    def test_purge1(self):
        res = xml_purge_nswrapper(XML1)
        self.assertNotIn("nswrapper", pycompat.to_text(res))

    def test_purge2(self):
        res = xml_purge_nswrapper(XML2)
        self.assertNotIn("nswrapper", pycompat.to_text(res))

    def test_purge3(self):
        res = xml_purge_nswrapper(ORDER_RESP_WRAPPER_TMPL.format(XML2))
        self.assertNotIn("nswrapper", pycompat.to_text(res))
