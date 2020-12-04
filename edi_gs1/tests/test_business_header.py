# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from freezegun import freeze_time

from .common import BaseTestCase

BH_NS = "http://www.unece.org/cefact/namespaces/StandardBusinessDocumentHeader"


class BusinessHeaderTestCase(BaseTestCase):

    _schema_path = "edi_gs1:static/schemas/sbdh/StandardBusinessDocumentHeader.xsd"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_records()

    @classmethod
    def _setup_records(cls):
        cls.bh_tmpl = cls.env.ref("edi_gs1.edi_exchange_template_business_header")
        vals = {
            "backend_id": cls.backend.id,
            "backend_type_id": cls.backend.backend_type_id.id,
            "name": "Template output 1",
            "direction": "output",
            "code": "test_type_out1",
            "exchange_file_ext": "txt",
            "exchange_filename_pattern": "{record.ref}-{type.code}-{dt}",
        }
        cls.exc_type = cls.env["edi.exchange.type"].create(vals)
        cls.related_record = cls.env.ref("base.partner_demo")
        vals = {
            # Does not really matter which record we bind the exchange to
            "model": cls.related_record._name,
            "res_id": cls.related_record.id,
            "type_id": cls.exc_type.id,
        }
        cls.exc_record = cls.backend.create_record("test_type_out1", vals)

    def test_template_render_values(self):
        values = self.bh_tmpl._get_render_values(self.exc_record)
        expected = {
            "backend": self.backend,
            "exchange_record": self.exc_record,
            "instance_identifier": self.exc_record.identifier,
            "record": self.related_record,
            "template": self.bh_tmpl,
        }
        for k, v in expected.items():
            self.assertEqual(values[k], v)

    @freeze_time("2020-07-08 07:30:00")
    def test_xml(self):
        output = self.bh_tmpl.generate_output(
            self.exc_record, sender=self.lsc_partner, receiver=self.lsp_partner,
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
            ns=BH_NS,
            sender=self.lsc_partner,
            receiver=self.lsp_partner,
            identifier=self.exc_record.identifier,
            date="2020-07-08T07:30:00",
        )
        self.assertXmlEquivalentOutputs(self.flatten(output), self.flatten(expected))
        handler = self._get_xml_handler()
        self.assertEqual(handler.validate(output), None)
