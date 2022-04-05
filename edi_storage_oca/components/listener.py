# Copyright 2021 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import functools
from pathlib import PurePath

from odoo.addons.component.core import Component


class EdiStorageListener(Component):
    _name = "edi.storage.component.listener"
    _inherit = "base.event.listener"

    def _move_file(self, storage, from_dir_str, to_dir_str, filename):
        from_dir = PurePath(from_dir_str)
        to_dir = PurePath(to_dir_str)
        if filename not in storage.list_files(from_dir.as_posix()):
            # The file might have been moved after a previous error.
            return False
        self._add_after_commit_hook(
            storage._move_files, [(from_dir / filename).as_posix()], to_dir.as_posix()
        )
        return True

    def _add_after_commit_hook(self, move_func, sftp_filepath, sftp_destination_path):
        """Add hook after commit to move the file when transaction is over."""
        self.env.cr.after(
            "commit",
            functools.partial(move_func, sftp_filepath, sftp_destination_path),
        )

    def on_edi_exchange_done(self, record):
        """Tries to move the file from pending directory to done directory"""
        backend = record.backend_id
        storage = backend.storage_id
        if not storage:
            return False
        direction = record.direction
        pending_dir, done_dir, error_dir = backend._get_storage_dirs(direction)
        if not done_dir:
            return False
        file = record.exchange_filename
        # If a file failed previously, it should have been moved to the error
        # dir. Therefore, it is not present in the pending dir, and we need to
        # retry from error dir.
        res = self._move_file(storage, pending_dir, done_dir, file)
        if not res:
            res = self._move_file(storage, error_dir, done_dir, file)
        return res

    def on_edi_exchange_error(self, record):
        """Tries to move the file from pending directory to error directory"""
        backend = record.backend_id
        storage = backend.storage_id
        if not storage:
            return False
        direction = record.direction
        pending_dir, done_dir, error_dir = backend._get_storage_dirs(direction)
        if not error_dir:
            return False
        file = record.exchange_filename
        return self._move_file(storage, pending_dir, error_dir, file)
