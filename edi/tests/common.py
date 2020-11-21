# Copyright 2020 ACSONE
# Copyright 2020 Creu Blanca
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
import os
from contextlib import contextmanager

from mock import patch

from odoo import fields
from odoo.tests.common import SavepointCase, tagged


@tagged("-at_install", "post_install")
class EDIBackendCommonTestCase(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context, tracking_disable=True, test_queue_job_no_delay=True
            )
        )
        cls.backend = cls._get_backend()
        cls.backend_model = cls.env["edi.backend"]
        cls.backend_type_model = cls.env["edi.backend.type"]
        cls.exchange_type_in = cls._create_exchange_type(
            name="Test CSV input",
            code="test_csv_input",
            direction="input",
            exchange_file_ext="csv",
            exchange_filename_pattern="{record.ref}-{type.code}-{dt}",
        )
        cls.exchange_type_out = cls._create_exchange_type(
            name="Test CSV output",
            code="test_csv_output",
            direction="output",
            exchange_file_ext="csv",
            exchange_filename_pattern="{record.ref}-{type.code}-{dt}",
        )
        cls.partner = cls.env.ref("base.res_partner_1")
        cls.partner.ref = "EDI_EXC_TEST"

    @contextmanager
    def mocked_today(self, forced_today):
        """ Helper to make easily a python "with statement" mocking the "today" date.
        :param forced_today: The expected "today" date as a str or Date object.
        :return: An object to be used like 'with self.mocked_today(<today>):'.
        """

        if isinstance(forced_today, str):
            forced_today_date = fields.Date.from_string(forced_today)
            forced_today_datetime = fields.Datetime.from_string(forced_today)
        elif isinstance(forced_today, datetime.datetime):
            forced_today_datetime = forced_today
            forced_today_date = forced_today_datetime.date()
        else:
            forced_today_date = forced_today
            forced_today_datetime = datetime.datetime.combine(
                forced_today_date, datetime.time()
            )

        def today(*args, **kwargs):
            return forced_today_date

        with patch.object(fields.Date, "today", today):
            with patch.object(fields.Date, "context_today", today):
                with patch.object(
                    fields.Datetime, "now", return_value=forced_today_datetime
                ):
                    yield

    def read_test_file(self, filename):
        path = os.path.join(os.path.dirname(__file__), "examples", filename)
        with open(path, "r") as thefile:
            return thefile.read()

    @classmethod
    def _get_backend(cls):
        return cls.env.ref("edi.demo_edi_backend")

    @classmethod
    def _create_exchange_type(cls, **kw):
        model = cls.env["edi.exchange.type"]
        vals = {
            "name": "Test CSV exchange",
            "backend_id": cls.backend.id,
            "backend_type_id": cls.backend.backend_type_id.id,
        }
        vals.update(kw)
        return model.create(vals)
