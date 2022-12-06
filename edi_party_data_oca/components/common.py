# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tools import DotDict

from odoo.addons.component.core import AbstractComponent


class EDIExchangePartyDataMixin(AbstractComponent):
    """Abstract component mixin provide partner data for exchanges."""

    _name = "edi.party.data.mixin"
    _inherit = "edi.component.mixin"
    _collection = "edi.backend"
    _usage = "edi.party.data"

    def __init__(self, work_context):
        super().__init__(work_context)
        self.partner = self._get_partner()
        self.allowed_id_categories = self.exchange_record.type_id.id_category_ids

    def _get_partner(self):
        # Hook here to define different logic to lookup for the partner
        # based on current partner (eg: pick the parent).
        return self.work.partner

    def get_party(self):
        """Return party information.

        Requires a res.partner to be passed via work context.

        :return: odoo.tools.DotDict
        """
        return self._party_from_partner()

    def _party_from_partner(self, **kw):
        # NB: for UBL this should probably replace `base.ubl._ubl_get_party_identification`
        # which does nothing today.
        party = DotDict(
            name=self._get_name(),
            identifiers=self._get_identifiers(),
            # TODO: is this only for UBL?
            endpoint=self._get_endpoint(),
        )
        party.update(kw)
        return party

    def _get_name(self):
        name_field = getattr(self.work, "party_data_name_field", "display_name")
        return self.partner[name_field]

    def _get_endpoint(self):
        return {}

    def _get_identifiers(self):
        identifiers = self.partner.id_numbers.filtered(
            lambda x: self._filter_id_number(x)
        )
        return [self._get_indentity(x) for x in identifiers]

    def _filter_id_number(self, id_number):
        if self.allowed_id_categories:
            return id_number.category_id in self.allowed_id_categories
        return True

    def _get_indentity(self, id_number):
        return DotDict(
            attrs={
                "schemeID": id_number.category_id.code,
            },
            value=id_number.name,
        )
