# Copyright 2021 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import errno
import io
import logging
import os
import ssl
from contextlib import contextmanager
from io import BytesIO

from odoo.exceptions import UserError

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)

try:
    import ftplib
except ImportError as err:  # pragma: no cover
    _logger.debug(err)

FTP_SECURITY_TO_PROTOCOL = {
    "tls": ssl.PROTOCOL_TLS,
    "tlsv1": ssl.PROTOCOL_TLSv1,
    "tlsv1_1": ssl.PROTOCOL_TLSv1_1,
    "tlsv1_2": ssl.PROTOCOL_TLSv1_2,
    "sslv2": "sslv2 has been deprecated due to security issues",
    "sslv23": ssl.PROTOCOL_SSLv23,
    "sslv3": "sslv3 has been deprecated due to security issues",
}


def ftp_mkdirs(client, path):
    try:
        client.mkd(path)
    except IOError as e:
        if e.errno == errno.ENOENT and path:
            ftp_mkdirs(client, os.path.dirname(path))
            client.mkd(path)
        else:
            raise  # pragma: no cover


@contextmanager
def ftp(backend):
    params = {}
    security = None
    if backend.ftp_encryption == "ftp":
        ftp = ftplib.FTP
    elif backend.ftp_encryption == "tls":
        ftp = ftplib.FTP_TLS
        # Due to a bug into between ftplib and ssl, this part (about ssl) might not work!
        # https://bugs.python.org/issue31727
        security = FTP_SECURITY_TO_PROTOCOL.get(backend.ftp_security, None)
        if isinstance(security, str):
            raise UserError(security)
        if security:
            ctx = ssl._create_stdlib_context(security)
            params.update({"context": ctx})
    else:
        raise NotImplementedError()
    with ftp(**params) as client:
        client.connect(host=backend.ftp_server, port=backend.ftp_port)
        if security:
            client.auth()
        client.login(backend.ftp_login, backend.ftp_password)
        if security:
            client.ssl_version = security
            client.prot_p()
        if backend.ftp_passive:
            client.set_pasv(True)
        yield client


class FTPStorageBackendAdapter(Component):
    _name = "ftp.adapter"
    _inherit = "base.storage.adapter"
    _usage = "ftp"

    def add(self, relative_path, data, **kwargs):
        with ftp(self.collection) as client:
            full_path = self._fullpath(relative_path)
            dirname = os.path.dirname(full_path)
            if dirname:
                try:
                    client.cwd(dirname)
                except IOError as e:
                    if e.errno == errno.ENOENT:
                        ftp_mkdirs(client, dirname)
                    else:
                        raise  # pragma: no cover
            with io.BytesIO(data) as tmp_file:
                try:
                    client.storbinary("STOR " + full_path, tmp_file)
                except ftplib.Error as e:
                    raise ValueError(repr(e))
                except OSError as e:
                    raise ValueError(repr(e))

    def get(self, relative_path, **kwargs):
        full_path = self._fullpath(relative_path)
        with ftp(self.collection) as client, BytesIO() as buff:
            try:
                client.retrbinary("RETR " + full_path, buff.write)
                data = buff.getvalue()
            except ftplib.Error as e:
                raise FileNotFoundError(repr(e))
        return data

    def list(self, relative_path):
        full_path = self._fullpath(relative_path)
        with ftp(self.collection) as client:
            try:
                return client.nlst(full_path)
            except IOError as e:
                if e.errno == errno.ENOENT:
                    # The path do not exist return an empty list
                    return []
                else:
                    raise  # pragma: no cover

    def move_files(self, files, destination_path):
        _logger.debug("mv %s %s", files, destination_path)
        with ftp(self.collection) as client:
            for ftp_file in files:
                dest_file_path = os.path.join(
                    destination_path, os.path.basename(ftp_file)
                )
                # Remove existing file at the destination path (an error is raised
                # otherwise)
                result = []
                try:
                    result = client.nlst(dest_file_path)
                except ftplib.Error:
                    _logger.debug("destination %s is free", dest_file_path)
                if result:
                    client.delete(dest_file_path)
                # Move the file
                client.rename(ftp_file, dest_file_path)

    def delete(self, relative_path):
        full_path = self._fullpath(relative_path)
        with ftp(self.collection) as client:
            return client.delete(full_path)

    def validate_config(self):
        with ftp(self.collection) as client:
            client.getwelcome()
