# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class EDIStorageReceiveComponent(Component):

    _name = "edi.storage.component.receive"
    _inherit = [
        "edi.component.receive.mixin",
        "edi.storage.component.mixin",
    ]
    _usage = "storage.receive"

    def receive(self):
        # If the file has been sent already, refresh its state
        # TODO: double check if this is useless
        # since the backend checks the state already
        checker = self.component(usage="storage.check")
        result = checker.check()
        if not result:
            # all good here
            return True

        direction = self.exchange_record.direction
        # Just the root of the incoming folder
        path = self._remote_file_path(direction, "pending", "")
        filename_pattern = self._get_filename_pattern()
        # TODO: add test
        # This particular test requires further mocking in `edi_storage.tests.common`
        filepaths = self.storage_id.find_files(filename_pattern, relative_path=path)
        if filepaths:
            filepath = filepaths[0]
            return self.storage.get(filepath)
        return False

    # TODO: add test
    def _get_filename_pattern(self):
        filename_pattern = self.exchange_record.type_id.exchange_filename_pattern
        if not filename_pattern:
            # By convention the filename will be
            # parent.filename + .ack.ext
            parent = self.exchange_record.parent_id
            ext = parent.type_id.exchange_file_ext.strip(".")
            filename_pattern = parent.exchange_filename.replace(
                "." + ext, ".ack" + "." + ext
            )
        return filename_pattern
