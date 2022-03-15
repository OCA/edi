# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from pathlib import PurePath

from odoo.addons.component.core import AbstractComponent


class EDIStorageComponentMixin(AbstractComponent):

    _name = "edi.storage.component.mixin"
    _inherit = "edi.component.mixin"
    # Components having `_storage_backend_type` will have precedence.
    # If the value is not set, generic components will be used.
    _storage_backend_type = None

    @classmethod
    def _component_match(cls, work, usage=None, model_name=None, **kw):
        res = super()._component_match(work, usage=usage, model_name=model_name, **kw)
        storage_type = kw.get("storage_backend_type")
        if storage_type and cls._storage_backend_type:
            return cls._storage_backend_type == storage_type
        return res

    @property
    def storage(self):
        return self.backend.storage_id

    def _dir_by_state(self, direction, state):
        """Return remote directory path by direction and state.

        :param direction: string stating direction of the exchange
        :param state: string stating state of the exchange
        :return: PurePath object
        """
        assert direction in ("input", "output")
        assert state in ("pending", "done", "error")
        return PurePath(
            (self.backend[direction + "_dir_" + state] or "").strip().rstrip("/")
        )

    def _remote_file_path(self, direction, state, filename):
        """Return remote file path by direction and state for give filename.

        :param direction: string stating direction of the exchange
        :param state: string stating state of the exchange
        :param filename: string for file name
        :return: PurePath object
        """
        return self._dir_by_state(direction, state) / filename.strip("/ ")

    def _get_remote_file(self, state, filename=None, binary=False):
        """Get file for current exchange_record in the given destination state.

        :param state: string ("pending", "done", "error")
        :param filename: custom file name, exchange_record filename used by default
        :return: remote file content as string
        """
        filename = filename or self.exchange_record.exchange_filename
        path = self._remote_file_path(self.exchange_record.direction, state, filename)
        try:
            # TODO: support match via pattern (eg: filename-prefix-*)
            # otherwise is impossible to retrieve input files and acks
            # (the date will never match)
            return self.storage.get(path.as_posix(), binary=binary)
        except FileNotFoundError:
            return None
