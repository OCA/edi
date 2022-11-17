# Copyright 2021 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# pylint: disable=missing-manifest-dependency
# disable warning on 'vcr' missing in manifest: this is only a dependency for
# dev/tests

import errno
import ftplib
import logging
import os

from unittest import mock

from odoo.addons.storage_backend.tests.common import BackendStorageTestMixin, CommonCase

_logger = logging.getLogger(__name__)

MOD_PATH = "odoo.addons.storage_backend_ftp.components.ftp_adapter"
ADAPTER_PATH = MOD_PATH + ".FTPStorageBackendAdapter"
FTP_LIB_PATH = MOD_PATH + ".ftplib"


class FtpCase(CommonCase, BackendStorageTestMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.write(
            {
                "backend_type": "ftp",
                "ftp_login": os.environ.get("FTP_LOGIN", "foo"),
                "ftp_password": os.environ.get("FTP_PWD", "pass"),
                "ftp_server": os.environ.get("FTP_HOST", "localhost"),
                "ftp_port": os.environ.get("FTP_PORT", "21"),
                "directory_path": "upload",
                "ftp_encryption": "ftp",
            }
        )
        cls.case_with_subdirectory = "upload/subdirectory/here"

    @mock.patch(MOD_PATH + ".ftp_mkdirs")
    @mock.patch(FTP_LIB_PATH)
    def test_add(self, mocked_ftplib, mocked_mkdirs):
        client = mocked_ftplib.FTP().__enter__()
        # simulate errors
        exc = IOError()
        # general
        client.cwd.side_effect = exc
        with self.assertRaises(IOError):
            self.backend.add("fake/path", b"fake data")
        # not found
        exc.errno = errno.ENOENT
        client.cwd.side_effect = exc
        file_data = b"fake data"
        with mock.patch("io.BytesIO") as tmp_file:
            self.backend.add("fake/path", file_data)
            # mkdirs has been called
            mocked_mkdirs.assert_called()
            client.storbinary.assert_called()
            tmp_file.assert_called()
            tmp_file.assert_called_with(file_data)
        client.storbinary.assert_called_with(
            "STOR upload/fake/path", tmp_file().__enter__()
        )

    @mock.patch(FTP_LIB_PATH)
    def test_get(self, mocked_ftplib):
        client = mocked_ftplib.FTP().__enter__()
        content = b"filecontent"
        with open("/tmp/fakefile2.txt", "w+b") as fakefile:
            fakefile.write(content)

        def side_effect_retrbinary(*args, **kwargs):
            """
            Mock function to read tmp file.
            """
            cmd, buff_write = args
            with open("/tmp/fakefile2.txt", "rb") as tmp_file:
                buff_write(tmp_file.read())

        client.retrbinary.side_effect = side_effect_retrbinary
        self.assertEqual(self.backend.get("fake/path"), content)

    @mock.patch(FTP_LIB_PATH)
    def test_list(self, mocked_ftplib):
        client = mocked_ftplib.FTP().__enter__()
        # simulate errors
        exc = IOError()
        # general
        client.nlst.side_effect = exc
        with self.assertRaises(IOError):
            self.backend.list_files()
        # not found
        exc.errno = errno.ENOENT
        client.nlst.side_effect = exc
        self.assertEqual(self.backend.list_files(), [])

    def test_find_files(self):
        good_filepaths = ["somepath/file%d.good" % x for x in range(1, 10)]
        bad_filepaths = ["somepath/file%d.bad" % x for x in range(1, 10)]
        mocked_filepaths = bad_filepaths + good_filepaths
        backend = self.backend.sudo()
        expected = good_filepaths[:]
        expected = [backend.directory_path + "/" + path for path in good_filepaths]
        self._test_find_files(
            backend, ADAPTER_PATH, mocked_filepaths, r".*\.good$", expected
        )

    # Do not patch the entire ftplib otherwise the error_perm Exception
    # become also a mock and then a traceback is generated on the "except ftplib.error_perm"
    # because this ftplib.error_perm is not really an Exception (but a mock)!
    @mock.patch(FTP_LIB_PATH + ".FTP")
    def test_move_files(self, mocked_ftplib):
        client = mocked_ftplib().__enter__()
        # simulate file is not already there
        client.nlst.side_effect = ftplib.error_perm()
        to_move = "move/from/path/myfile.txt"
        to_path = "move/to/path"
        self.backend.move_files([to_move], to_path)
        # no need to delete it
        client.delete.assert_not_called()
        # rename gets called
        client.rename.assert_called_with(to_move, to_move.replace("from", "to"))
        # now try to override destination
        client.nlst.side_effect = None
        client.nlst.return_value = True
        self.backend.move_files([to_move], to_path)
        # client will delete it first
        client.delete.assert_called_with(to_move.replace("from", "to"))
        # then move it
        client.rename.assert_called_with(to_move, to_move.replace("from", "to"))

    @mock.patch(FTP_LIB_PATH)
    def test_delete(self, mocked_ftplib):
        client = mocked_ftplib.FTP().__enter__()
        path = "delete/a/path"
        self.backend.delete(path)
        client.delete.assert_called_with(
            os.path.join(self.backend.directory_path, path)
        )

    @mock.patch(FTP_LIB_PATH)
    def test_validate_config(self, mocked_ftplib):
        client = mocked_ftplib.FTP().__enter__()
        self.backend.action_test_config()
        client.getwelcome.assert_called()

    @mock.patch(FTP_LIB_PATH)
    def test_mkd(self, mocked_ftplib):
        client = mocked_ftplib.FTP().__enter__()
        # simulate errors
        exc = IOError()
        exc.errno = errno.ENOENT
        # general
        client.cwd.side_effect = exc
        client.mkd.side_effect = exc
        with self.assertRaises(OSError):
            self.backend.add("fake/path", b"fake data")
        client.mkd.assert_called()
