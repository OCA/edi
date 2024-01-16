# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import base64

import chardet

from .common import EDIBackendCommonComponentRegistryTestCase
from .fake_components import FakeOutputGenerator


class EDIBackendTestOutputCase(EDIBackendCommonComponentRegistryTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_components(
            cls,
            FakeOutputGenerator,
        )
        vals = {
            "model": cls.partner._name,
            "res_id": cls.partner.id,
        }
        cls.record = cls.backend.create_record("test_csv_output", vals)

    def setUp(self):
        super().setUp()
        FakeOutputGenerator.reset_faked()

    def test_encoding_default(self):
        """
        Test default output/input encoding (UTF-8). Use string with special
        character to test the encoding applied.
        """
        self.backend.with_context(fake_output="Palmotićeva").exchange_generate(
            self.record
        )
        # Test decoding is applied correctly
        self.assertEqual(self.record._get_file_content(), "Palmotićeva")
        # Test encoding used
        content = base64.b64decode(self.record.exchange_file)
        encoding = chardet.detect(content)["encoding"].lower()
        self.assertEqual(encoding, "utf-8")

    def test_encoding(self):
        """
        Test specific output/input encoding. Use string with special
        character to test the encoding applied.
        """
        self.exchange_type_out.write({"encoding": "UTF-16"})
        self.backend.with_context(fake_output="Palmotićeva").exchange_generate(
            self.record
        )
        # Test decoding is applied correctly
        self.assertEqual(self.record._get_file_content(), "Palmotićeva")
        # Test encoding used
        content = base64.b64decode(self.record.exchange_file)
        encoding = chardet.detect(content)["encoding"].lower()
        self.assertEqual(encoding, "utf-16")

    def test_encoding_error_handler(self):
        self.exchange_type_out.write({"encoding": "ascii"})
        # By default, error handling raises error
        with self.assertRaises(UnicodeEncodeError):
            self.backend.with_context(fake_output="Palmotićeva").exchange_generate(
                self.record
            )
        self.exchange_type_out.write({"encoding_out_error_handler": "ignore"})
        self.backend.with_context(fake_output="Palmotićeva").exchange_generate(
            self.record
        )
        self.assertEqual(self.record._get_file_content(), "Palmotieva")

    def test_decoding_error_handler(self):
        self.backend.with_context(fake_output="Palmotićeva").exchange_generate(
            self.record
        )
        # Change encoding to ascii to check the decoding
        self.exchange_type_out.write({"encoding": "ascii"})
        # By default, error handling raises error
        with self.assertRaises(UnicodeDecodeError):
            content = self.record._get_file_content()
        self.exchange_type_out.write({"encoding_in_error_handler": "ignore"})
        content = self.record._get_file_content()
        self.assertEqual(content, "Palmotieva")
