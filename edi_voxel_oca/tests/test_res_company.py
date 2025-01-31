# Copyright 2019 Tecnativa - Ernesto Tejeda
# Copyright 2025 Guavana - Leonardo J. Caballero G.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

import pytz

from odoo.tests.common import TransactionCase


class TestResCompany(TransactionCase):
    def setUp(self):
        super(TestResCompany, self).setUp()
        self.company = self.env["res.company"].create(
            {
                "name": "Test Company",
                "voxel_enabled": True,
                "voxel_send_mode": "fixed",
                "voxel_sent_time": 11.0,  # 11:00 AM
                "voxel_delay_time": 2.0,
            }
        )

    def test_get_voxel_report_eta_auto(self):
        self.company.voxel_send_mode = "auto"
        eta = self.company._get_voxel_report_eta()
        self.assertIsNone(eta, "ETA should be None for auto send mode")

    def test_get_voxel_report_eta_fixed(self):
        tz = pytz.timezone(self.env.user.partner_id.tz or "UTC")
        now = datetime.now(tz)
        expected_eta = now.replace(hour=11, minute=0, second=0, microsecond=0)
        if now.hour > 11 or (now.hour == 11 and now.minute > 0):
            expected_eta += timedelta(days=1)
        eta = self.company._get_voxel_report_eta()
        eta = eta.replace(second=0, microsecond=0)  # Ignore seconds and microseconds
        self.assertEqual(eta, expected_eta, "ETA should match the expected fixed time")

    def test_get_voxel_report_eta_delayed(self):
        self.company.voxel_send_mode = "delayed"
        expected_eta = datetime.now() + timedelta(hours=2)
        eta = self.company._get_voxel_report_eta()
        self.assertIsNotNone(eta, "ETA should not be None for delayed send mode")
        self.assertAlmostEqual(
            eta,
            expected_eta,
            msg="ETA should be 2 hours from now for delayed send mode",
            delta=timedelta(seconds=1),
        )
