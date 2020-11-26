# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import tagged

from .common import EDIBackendCommonComponentRegistryTestCase
from .fake_components import FakeOutputChecker, FakeOutputGenerator, FakeOutputSender


@tagged("-at_install", "post_install")
class EDIBackendTestCase(EDIBackendCommonComponentRegistryTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_components(
            cls, FakeOutputGenerator, FakeOutputSender, FakeOutputChecker
        )
        cls.partner2 = cls.env.ref("base.res_partner_10")
        cls.partner3 = cls.env.ref("base.res_partner_12")
        cls.record1 = cls.backend.create_record(
            "test_csv_output", {"model": cls.partner._name, "res_id": cls.partner.id}
        )
        cls.record2 = cls.backend.create_record(
            "test_csv_output", {"model": cls.partner._name, "res_id": cls.partner2.id}
        )
        cls.record3 = cls.backend.create_record(
            "test_csv_output", {"model": cls.partner._name, "res_id": cls.partner3.id}
        )
        cls.records = cls.record1 + cls.record1 + cls.record3

    def test_generate_output_new_no_auto(self):
        # No content ready to be sent, no auto-generate, nothing happens
        for rec in self.records:
            self.assertEqual(rec.edi_exchange_state, "new")
        self.backend._cron_check_output_exchange_sync()
        for rec in self.records:
            self.assertEqual(rec.edi_exchange_state, "new")

    def test_generate_output_new_auto_skip_send(self):
        self.exchange_type_out.exchange_file_auto_generate = True
        # No content ready to be sent, will get the content but not send it
        for rec in self.records:
            self.assertEqual(rec.edi_exchange_state, "new")
        self.backend._cron_check_output_exchange_sync(skip_send=True)
        for rec in self.records:
            self.assertEqual(rec.edi_exchange_state, "output_pending")
            self.assertEqual(rec._get_output(), "FAKE_OUTPUT: %s" % rec.id)

    def test_generate_output_new_auto_send(self):
        self.exchange_type_out.exchange_file_auto_generate = True
        # No content ready to be sent, will get the content and send it
        for rec in self.records:
            self.assertEqual(rec.edi_exchange_state, "new")
        self.backend._cron_check_output_exchange_sync()
        for rec in self.records:
            self.assertEqual(rec.edi_exchange_state, "output_sent")
            self.assertEqual(rec._get_output(), "FAKE_OUTPUT: %s" % rec.id)

    def test_generate_output_output_ready_auto_send(self):
        # No content ready to be sent, will get the content and send it
        for rec in self.records:
            self.assertEqual(rec.edi_exchange_state, "new")
        self.record1._set_output("READY")
        self.record1.edi_exchange_state = "output_sent"
        self.backend.with_context(
            test_output_check_update_values={
                "edi_exchange_state": "output_sent_and_processed"
            }
        )._cron_check_output_exchange_sync()
        for rec in self.records - self.record1:
            self.assertEqual(rec.edi_exchange_state, "new")
        self.assertEqual(self.record1.edi_exchange_state, "output_sent_and_processed")
