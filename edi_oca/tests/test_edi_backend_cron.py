# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tools import mute_logger

from .common import EDIBackendCommonComponentRegistryTestCase
from .fake_components import FakeOutputChecker, FakeOutputGenerator, FakeOutputSender

LOGGERS = ("odoo.addons.edi_oca.models.edi_backend", "odoo.addons.queue_job.delay")


class EDIBackendTestCronCase(EDIBackendCommonComponentRegistryTestCase):
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

    def setUp(self):
        super().setUp()
        FakeOutputGenerator.reset_faked()
        FakeOutputSender.reset_faked()
        FakeOutputChecker.reset_faked()

    @mute_logger(*LOGGERS)
    def test_exchange_generate_new_no_auto(self):
        # No content ready to be sent, no auto-generate, nothing happens
        for rec in self.records:
            self.assertEqual(rec.edi_exchange_state, "new")
        self.backend._cron_check_output_exchange_sync()
        for rec in self.records:
            self.assertEqual(rec.edi_exchange_state, "new")

    @mute_logger(*LOGGERS)
    def test_exchange_generate_new_auto_skip_send(self):
        self.exchange_type_out.exchange_file_auto_generate = True
        # No content ready to be sent, will get the content but not send it
        for rec in self.records:
            self.assertEqual(rec.edi_exchange_state, "new")
        self.backend._cron_check_output_exchange_sync(skip_send=True)
        for rec in self.records:
            self.assertEqual(rec.edi_exchange_state, "output_pending")
            self.assertTrue(FakeOutputGenerator.check_called_for(rec))
            self.assertEqual(
                rec._get_file_content(), FakeOutputGenerator._call_key(rec)
            )
            # TODO: test better?
            self.assertFalse(rec.ack_exchange_id)

    @mute_logger(*LOGGERS)
    def test_exchange_generate_new_auto_send(self):
        self.exchange_type_out.exchange_file_auto_generate = True
        # No content ready to be sent, will get the content and send it
        for rec in self.records:
            self.assertEqual(rec.edi_exchange_state, "new")
        self.backend._cron_check_output_exchange_sync()
        for rec in self.records:
            self.assertEqual(rec.edi_exchange_state, "output_sent")
            self.assertTrue(FakeOutputGenerator.check_called_for(rec))
            self.assertEqual(
                rec._get_file_content(), FakeOutputGenerator._call_key(rec)
            )
            self.assertTrue(FakeOutputSender.check_called_for(rec))

    @mute_logger(*LOGGERS)
    def test_exchange_generate_output_ready_auto_send(self):
        # No content ready to be sent, will get the content and send it
        for rec in self.records:
            self.assertEqual(rec.edi_exchange_state, "new")
        self.record1._set_file_content("READY")
        self.record1.edi_exchange_state = "output_sent"
        self.backend.with_context(
            fake_update_values={"edi_exchange_state": "output_sent_and_processed"}
        )._cron_check_output_exchange_sync(skip_sent=False)
        for rec in self.records - self.record1:
            self.assertEqual(rec.edi_exchange_state, "new")
        self.assertEqual(self.record1.edi_exchange_state, "output_sent_and_processed")
        self.assertTrue(FakeOutputGenerator.check_not_called_for(self.record1))
        self.assertTrue(FakeOutputSender.check_not_called_for(self.record1))
        self.assertTrue(FakeOutputChecker.check_called_for(self.record1))
