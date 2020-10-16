# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from mock import patch

from odoo.tools.misc import mute_logger

from odoo.addons.test_mail.tests.common import MockEmails


class TestEdi(MockEmails):
    @classmethod
    def setUpClass(cls):
        super(TestEdi, cls).setUpClass()
        cls.format = cls.env["edi.format"].create(
            {
                "name": "TEST",
                "usage": "TEST",
                "can_send": True,
                "can_receive": True,
                "format_key": "mail",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Partner"})

    def test_edi(self):
        with patch.object(
            self.partner,
            "_get_edi_mail_file",
            lambda: (b"HOLA", "DEMO.txt", "application/txt", "txt"),
            create=True,
        ):
            self.format._generate_document(self.partner)
        document = self.env["edi.document"].search(
            [("res_model", "=", self.partner._name), ("res_id", "=", self.partner.id)]
        )
        self.assertTrue(document)
        self.assertEqual(1, len(document.message_ids))
        self.assertFalse(document.error)
        with mute_logger("odoo.addons.edi.models.edi_document"):
            document.action_send()
        self.assertTrue(document.error)
        self.assertEqual(1, len(document.message_ids))
        # pylint: disable=C8107
        with patch(
            "odoo.addons.edi.models.edi_format.EdiFormat._send_mail",
            lambda r, doc: self.env[doc.res_model]
            .browse(doc.res_id)
            .message_post(body="THIS IS A DEMO MESSAGE")
            .write({"model": doc._name, "res_id": doc.id}),
            create=True,
        ):
            document.action_send()
        self.assertEqual(3, len(document.message_ids))
