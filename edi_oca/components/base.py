# Copyright 2020 ACSONE
# @author: Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.component.core import AbstractComponent


class EDIBackendComponentMixin(AbstractComponent):

    _name = "edi.component.mixin"
    _collection = "edi.backend"
    _usage = None
    _backend_type = None
    _exchange_type = None

    def __init__(self, work_context):
        super().__init__(work_context)
        self.backend = work_context.backend
        self.exchange_record = work_context.exchange_record
        self.record = self.exchange_record.record
        self.type_settings = self.exchange_record.type_id.get_settings()

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
