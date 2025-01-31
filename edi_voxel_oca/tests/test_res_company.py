# Copyright 2019 Tecnativa - Ernesto Tejeda
# Copyright 2025 Guavana - Leonardo J. Caballero G.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from datetime import datetime, timedelta
import pytz

class TestResCompany(TransactionCase):

    def setUp(self):
        super(TestResCompany, self).setUp()
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
            'voxel_enabled': True,
            'voxel_send_mode': 'auto',
            'voxel_sent_time': 12.0,
            'voxel_delay_time': 2.0,
        })

    def test_get_voxel_report_eta_auto(self):
        self.company.voxel_send_mode = 'auto'
        eta = self.company._get_voxel_report_eta()
        self.assertIsNone(eta, "ETA should be None for auto send mode")

    def test_get_voxel_report_eta_fixed(self):
        self.company.voxel_send_mode = 'fixed'
        tz = self.env.context.get("tz", self.env.user.partner_id.tz) or 'UTC'
        offset = datetime.now(pytz.timezone(tz)).strftime("%z")
        hour_diff = int(offset[:3])
        expected_hour = int(12 - hour_diff)
        now = datetime.now()
        if now.hour > expected_hour:
            now += timedelta(days=1)
        expected_eta = now.replace(hour=expected_hour, minute=0, second=0, microsecond=0)
        eta = self.company._get_voxel_report_eta()
        self.assertEqual(eta, expected_eta, "ETA should match the expected fixed time")

    def test_get_voxel_report_eta_delayed(self):
        self.company.voxel_send_mode = 'delayed'
        expected_eta = datetime.now() + timedelta(hours=2)
        eta = self.company._get_voxel_report_eta()
        self.assertIsNotNone(eta, "ETA should not be None for delayed send mode")
        self.assertAlmostEqual(eta, expected_eta, msg="ETA should be 2 hours from now for delayed send mode", delta=timedelta(seconds=1))
