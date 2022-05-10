# Copyright 2020 ACSONE
# Copyright 2022 Camptocamp SA (https://www.camptocamp.com).
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from freezegun import freeze_time

from .common import EDIBackendCommonTestCase


class EDIExchangeTypeTestCase(EDIBackendCommonTestCase):
    def test_advanced_settings(self):
        settings = """
        components:
            foo: this
            boo: that
        whatever:
            ok: True
        """
        self.exchange_type_out.advanced_settings_edit = settings
        # fmt:off
        self.assertEqual(self.exchange_type_out.advanced_settings, {
            "components": {
                "foo": "this",
                "boo": "that",
            },
            "whatever": {
                "ok": True,
            }
        })
        # fmt:on

    def _test_exchange_filename(self, wanted_filename):
        filename = self.exchange_type_out._make_exchange_filename(
            exchange_record=self.env["edi.exchange.record"]
        )
        self.assertEqual(filename, wanted_filename)

    @freeze_time("2022-04-28 08:37:24")
    def test_filename_pattern_settings(self):
        """
        Test filename pattern defined into advanced settings.

        Example of pattern:
          filename_pattern:
            force_tz: Europe/Rome
            date_pattern: %Y-%m-%d-%H-%M-%S
        """

        self.env.user.tz = None
        self.exchange_type_out.write(
            {
                "exchange_filename_pattern": "Test-File",
                "exchange_file_ext": "csv",
                "advanced_settings_edit": None,
            }
        )

        # Test without any settings and minimal filename pattern
        self._test_exchange_filename("Test-File.csv")

        # Test with datetime in filename pattern
        self.exchange_type_out.exchange_filename_pattern = "Test-File-{dt}"
        self._test_exchange_filename("Test-File-2022-04-28-08-37-24.csv")

        # Add timezone on current user
        self.env.user.tz = "America/New_York"  # New_York time is -4h
        self._test_exchange_filename("Test-File-2022-04-28-04-37-24.csv")

        # Force date pattern on advanced settings
        self.exchange_type_out.advanced_settings_edit = """
        filename_pattern:
            date_pattern: '%Y-%m-%d-%H'
        """
        self._test_exchange_filename("Test-File-2022-04-28-04.csv")

        # Force timezone on advanced settings
        self.exchange_type_out.advanced_settings_edit = """
        filename_pattern:
            # Rome time is +2h
            force_tz: Europe/Rome
        """
        self._test_exchange_filename("Test-File-2022-04-28-10-37-24.csv")

        # Force date pattern and timezone on advanced settings
        self.exchange_type_out.advanced_settings_edit = """
        filename_pattern:
            # Rome time is +2h
            force_tz: Europe/Rome
            date_pattern: '%Y-%m-%d-%H-%M'
        """
        self._test_exchange_filename("Test-File-2022-04-28-10-37.csv")
