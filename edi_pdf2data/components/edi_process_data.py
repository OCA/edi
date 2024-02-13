# Copyright 2021 Creu Blanca
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.component.core import AbstractComponent


class EDIBackendInputComponentMixin(AbstractComponent):
    """Generate input content.
    """

    _name = "edi.component.process_data.mixin"
    _inherit = "edi.component.mixin"
    _usage = "process_data"
    _backend_type = "import_data"
    _exchange_type = "pdf2data"
    _process_type = None

    @classmethod
    def _component_match(cls, work, usage=None, model_name=None, **kw):
        res = super()._component_match(work, usage=usage, model_name=model_name, **kw)
        process_type = kw.get("process_type")
        return res and cls._process_type == process_type

    def process_data(self, data, template, file):
        raise NotImplementedError()
