# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from freezegun import freeze_time

from .common import BaseXMLTestCase


class BusinessHeaderTestCase(BaseXMLTestCase):
    def _get_handler(self, usage="gs1.StandardBusinessDocumentHeader", **kw):
        # FIXME: use a real record
        record = object()
        return self.backend._get_component(
            work_ctx=dict(
                record=record,
                sender=self.lsc_partner,
                receiver=self.lsp_partner,
                instance_identifier="TEST-DOC-XYZ",
            ),
            usage=usage,
            **kw
        )

    def test_header_version_data(self):
        handler = self._get_handler()
        result = handler._header_version()
        expected = {"HeaderVersion": {"@ns": "sh", "@value": "1.0"}}
        self.assertEqual(result, expected)

    def _expected_contact(self, key, record):
        ctype = "Buyer" if key == "Sender" else "Seller"
        return {
            key: {
                "@ns": "sh",
                "Identifier": {"@ns": "sh", "@attrs": {"Authority": "GS1"}},
                "ContactInformation": {
                    "@ns": "sh",
                    "Contact": {"@ns": "sh", "@value": record.name},
                    "EmailAddress": {"@ns": "sh", "@value": record.email},
                    "TelephoneNumber": {"@ns": "sh", "@value": record.phone},
                    "ContactTypeIdentifier": {"@ns": "sh", "@value": ctype},
                },
            },
        }

    def test_sender_data(self):
        handler = self._get_handler()
        result = handler._sender()
        expected = self._expected_contact("Sender", self.lsc_partner)
        self.assertEqual(result, expected)

    def test_receiver_data(self):
        handler = self._get_handler()
        result = handler._receiver()
        expected = self._expected_contact("Receiver", self.lsp_partner)
        self.assertEqual(result, expected)

    @freeze_time("2020-07-08 07:30:00")
    def test_document_id_data(self):
        handler = self._get_handler()
        result = handler._document_identification()
        expected = {
            "DocumentIdentification": {
                "@ns": "sh",
                "Standard": {"@ns": "sh", "@value": "GS1"},
                "TypeVersion": {"@ns": "sh", "@value": "3.4"},
                "InstanceIdentifier": {"@ns": "sh", "@value": "TEST-DOC-XYZ"},
                "Type": {"@ns": "sh", "@value": ""},
                "MultipleType": {"@ns": "sh", "@value": "false"},
                "CreationDateAndTime": {"@ns": "sh", "@value": "2020-07-08T07:30:00"},
            }
        }
        self.assertEqual(result, expected)

    @freeze_time("2020-07-08 07:30:00")
    def test_xml(self):
        handler = self._get_handler()
        result = handler.generate_xml()
        # namespace is include in main document root
        # but we need it to parse the result which would fail w/out this
        result = result.replace(
            "<sh:StandardBusinessDocumentHeader>",
            "<sh:StandardBusinessDocumentHeader xmlns:sh='{}'>".format(
                handler._xmlns["sh"]
            ),
        )
        expected = """
            <sh:StandardBusinessDocumentHeader xmlns:sh="{ns}">
                <sh:HeaderVersion>1.0</sh:HeaderVersion>
                <sh:Sender>
                    <sh:Identifier Authority="GS1"/>
                    <sh:ContactInformation>
                        <sh:Contact>{sender.name}</sh:Contact>
                        <sh:EmailAddress>{sender.email}</sh:EmailAddress>
                        <sh:TelephoneNumber>{sender.phone}</sh:TelephoneNumber>
                        <sh:ContactTypeIdentifier>Buyer</sh:ContactTypeIdentifier>
                    </sh:ContactInformation>
                </sh:Sender>
                <sh:Receiver>
                    <sh:Identifier Authority="GS1"/>
                    <sh:ContactInformation>
                        <sh:Contact>{receiver.name}</sh:Contact>
                        <sh:EmailAddress>{receiver.email}</sh:EmailAddress>
                        <sh:TelephoneNumber>{receiver.phone}</sh:TelephoneNumber>
                        <sh:ContactTypeIdentifier>Seller</sh:ContactTypeIdentifier>
                    </sh:ContactInformation>
                </sh:Receiver>
                <sh:DocumentIdentification>
                    <sh:Standard>GS1</sh:Standard>
                    <sh:TypeVersion>3.4</sh:TypeVersion>
                    <sh:InstanceIdentifier>{identifier}</sh:InstanceIdentifier>
                    <sh:Type/>
                    <sh:MultipleType>false</sh:MultipleType>
                    <sh:CreationDateAndTime>{date}</sh:CreationDateAndTime>
                </sh:DocumentIdentification>
            </sh:StandardBusinessDocumentHeader>
        """.format(
            ns=handler._xmlns["sh"],
            sender=self.lsc_partner,
            receiver=self.lsp_partner,
            identifier="TEST-DOC-XYZ",
            date="2020-07-08T07:30:00",
        )
        self.assertXmlEquivalentOutputs(self.flatten(result), self.flatten(expected))
        # when valid returns none
        self.assertFalse(handler.validate_schema(result))
