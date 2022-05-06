# Copyright 2022 Camptocamp SA (https://www.camptocamp.com).
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.edi_oca.tests.common import EDIBackendCommonTestCase


class EDIExchangeTypeTestCase(EDIBackendCommonTestCase):
    def _check_test_storage_fullpath(self, wanted_fullpath, directory, filename):
        fullpath = self.exchange_type_out._storage_fullpath(directory, filename)
        self.assertEqual(fullpath.as_posix(), wanted_fullpath)

    def _do_test_storage_fullpath(self, prefix=""):
        # Test with no directory and no filename
        wanted_fullpath = prefix or "."
        self._check_test_storage_fullpath(wanted_fullpath, None, None)

        # Test with directory
        directory = "test_directory"
        wanted_fullpath = f"{prefix}/{directory}" if prefix else directory
        self._check_test_storage_fullpath(wanted_fullpath, directory, None)

        # Test with filename
        filename = "test_filename.csv"
        wanted_fullpath = f"{prefix}/{filename}" if prefix else filename
        self._check_test_storage_fullpath(wanted_fullpath, None, filename)

        # Test with directory and filename
        wanted_fullpath = (
            f"{prefix}/{directory}/{filename}" if prefix else f"{directory}/{filename}"
        )
        self._check_test_storage_fullpath(wanted_fullpath, directory, filename)

    def test_storage_fullpath(self):
        """
        Test storage fullpath defined into advanced settings.
        Example of pattern:
          storage:
            # simple string
            path: path/to/file
            # name of the param containing the path
            path_config_param: path/to/file
        """

        # Test without any prefix
        self._do_test_storage_fullpath()

        # Force path on advanced settings
        prefix = "prefix/path"
        self.exchange_type_out.advanced_settings_edit = f"""
        storage:
            path: {prefix}
        """
        self._do_test_storage_fullpath(prefix=prefix)

        # Force path on advanced settings using config param, but not defined
        self.exchange_type_out.advanced_settings_edit = """
        storage:
            path_config_param: prefix_path_config_param
        """
        self._do_test_storage_fullpath()

        # Define config param
        prefix = "prefix/path/by/config/param"
        self.env["ir.config_parameter"].sudo().set_param(
            "prefix_path_config_param", prefix
        )
        self._do_test_storage_fullpath(prefix=prefix)
