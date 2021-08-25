# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

# import mock
# from freezegun import freeze_time

# from odoo import fields
# from odoo.exceptions import UserError
from odoo.tests.common import at_install, post_install
from odoo.addons.component.core import WorkContext, ComponentRegistry

from .common import EDIBackendCommonComponentRegistryTestCase
from .fake_components import FakeInputReceive


class EDIBackendTestCase(EDIBackendCommonComponentRegistryTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        vals = {
            "model": cls.partner._name,
            "res_id": cls.partner.id,
        }
        cls.record = cls.backend.create_record("test_csv_input", vals)

    @classmethod
    def _setup_context(cls):
        return dict(super()._setup_context(), _edi_receive_break_on_error=True)

    def setUp(self):
        super().setUp()
        self._build_components(
            # TODO: test all components lookup
            FakeInputReceive,
        )
        self.comp_registry.load_components("edi_oca")
        FakeInputReceive.reset_faked()

    @at_install(False)
    @post_install(True)
    def test_receive_record_nothing_todo(self):
        self.backend.with_context(fake_output="yeah!").exchange_receive(self.record)
        self.assertEqual(self.record._get_file_content(), "")
        self.assertEqual(self.record.edi_exchange_state, "new")

    @at_install(False)
    @post_install(True)
    def test_receive_record(self):
        self.record.edi_exchange_state = "input_pending"
        self.backend.with_context(fake_output="yeah!").exchange_receive(self.record)
        self.assertEqual(self.record._get_file_content(), "yeah!")
        self.assertEqual(self.record.edi_exchange_state, "input_received")
