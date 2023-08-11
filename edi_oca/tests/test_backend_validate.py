# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64

from ..exceptions import EDIValidationError
from .common import EDIBackendCommonComponentRegistryTestCase
from .fake_components import (
    FakeInputReceive,
    FakeInputValidate,
    FakeOutputGenerator,
    FakeOutputValidate,
)


class EDIBackendTestValidateCase(EDIBackendCommonComponentRegistryTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_components(
            # TODO: test all components lookup
            cls,
            FakeInputValidate,
            FakeOutputValidate,
            FakeInputReceive,
            FakeOutputGenerator,
        )
        vals = {
            "model": cls.partner._name,
            "res_id": cls.partner.id,
            "exchange_file": base64.b64encode(b"1234"),
        }
        cls.record_in = cls.backend.create_record("test_csv_input", vals)
        vals.pop("exchange_file")
        cls.record_out = cls.backend.create_record("test_csv_output", vals)

    def setUp(self):
        super().setUp()
        FakeInputValidate.reset_faked()
        FakeOutputValidate.reset_faked()
        FakeInputReceive.reset_faked()
        FakeOutputGenerator.reset_faked()

    def test_receive_validate_record(self):
        self.record_in.write({"edi_exchange_state": "input_pending"})
        self.backend.exchange_receive(self.record_in)
        self.assertTrue(FakeInputValidate.check_called_for(self.record_in))
        self.assertRecordValues(
            self.record_in, [{"edi_exchange_state": "input_received"}]
        )

    def test_receive_validate_record_error(self):
        self.record_in.write({"edi_exchange_state": "input_pending"})
        exc = EDIValidationError("Data seems wrong!")
        self.backend.with_context(test_break_validate=exc).exchange_receive(
            self.record_in
        )
        self.assertTrue(FakeInputValidate.check_called_for(self.record_in))
        self.assertRecordValues(
            self.record_in,
            [
                {
                    "edi_exchange_state": "validate_error",
                    "exchange_error": "Data seems wrong!",
                }
            ],
        )

    def test_generate_validate_record(self):
        self.record_out.write({"edi_exchange_state": "new"})
        self.backend.exchange_generate(self.record_out)
        self.assertTrue(FakeOutputValidate.check_called_for(self.record_out))
        self.assertRecordValues(
            self.record_out, [{"edi_exchange_state": "output_pending"}]
        )

    def test_generate_validate_record_error(self):
        self.record_out.write({"edi_exchange_state": "new"})
        exc = EDIValidationError("Data seems wrong!")
        self.backend.with_context(test_break_validate=exc).exchange_generate(
            self.record_out
        )
        self.assertTrue(FakeOutputValidate.check_called_for(self.record_out))
        self.assertRecordValues(
            self.record_out,
            [
                {
                    "edi_exchange_state": "validate_error",
                    "exchange_error": "Data seems wrong!",
                }
            ],
        )
