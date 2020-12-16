# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class EDIBackendComponentMixin(AbstractComponent):

    _name = "edi.component.mixin"
    _collection = "edi.backend"
    _usage = None
    _backend_type = None
    _exchange_type = None

    @property
    def exchange_record(self):
        return self.work.exchange_record

    @property
    def backend(self):
        return self.work.backend

    @property
    def record(self):
        return self.work.exchange_record.record

    @staticmethod
    def _match_attrs():
        """Attributes to be used for matching this component.

        By default, match by backend and exchange type.

        NOTE: the class attribute must have an underscore, the name here not.
        """
        return ("backend_type", "exchange_type")

    @classmethod
    def _component_match(cls, work, usage=None, model_name=None, **kw):
        """Override to customize match.

        Registry lookup filtered by usage and model_name when landing here.
        Now, narrow match to `_match_attrs` attributes.
        """
        match_attrs = cls._match_attrs()
        if not any([kw.get(k) for k in match_attrs]):
            # No attr to check
            return True

        backend_type = kw.get("backend_type")
        exchange_type = kw.get("exchange_type")

        if cls._backend_type and cls._exchange_type:
            # They must match both
            return (
                cls._backend_type == backend_type
                and cls._exchange_type == exchange_type
            )

        if cls._backend_type not in (None, kw.get("backend_type")):
            return False

        if cls._exchange_type not in (None, kw.get("exchange_type")):
            return False

        return True
