# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class EDIStorageSendComponent(Component):

    _name = "edi.storage.component.send"
    _inherit = [
        "edi.component.send.mixin",
        "edi.storage.component.mixin",
    ]
    _usage = "storage.send"

    def send(self):
        # If the file has been sent already, refresh its state
        # TODO: double check if this is useless
        # since the backend checks the state already
        checker = self.component(usage="storage.check")
        result = checker.check()
        if not result:
            # all good here
            return True

        direction = self.exchange_record.direction
        filename = self.exchange_record.exchange_filename
        filedata = self.exchange_record.exchange_file
        path = self._remote_file_path(direction, "pending", filename)
        self.storage.add(path.as_posix(), filedata, binary=False)
        # TODO: delegate this to generic storage backend
        # except paramiko.ssh_exception.AuthenticationException:
        #     # TODO this exc handling should be moved to sftp backend IMO
        #     error = _("Authentication error")
        #     state = "error_on_send"
        # TODO: catch other specific exceptions
        # this will swallow all the exceptions!
        return True
