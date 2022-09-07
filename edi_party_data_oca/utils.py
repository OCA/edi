# Copyright 2022 Camptocamp SA
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def get_party_data_component(exc_record, partner, work_ctx=None):
    """Shortcut to retrieve party data component."""
    work_ctx = work_ctx or {}
    work_ctx.update({"exchange_record": exc_record, "partner": partner})
    backend = exc_record.backend_id
    # TODO: match_attrs normally comes w/ `backend._get_component`
    # but ATM we cannot use it because the usage will be computed
    # by `_get_component_usage_candidates` which does not consider explicit usage.
    # We have 2 optins for improvements:
    # 1. allow `_get_component` to receive an explicit usage
    # 2. inject a new candidate in `_get_component_usage_candidates`
    # equal to the key that is passed.
    # @simahawk: I'd go for opt 1.
    match_attrs = backend._component_match_attrs(exc_record, "data")
    return backend._find_component(
        backend._name, ["edi.party.data"], work_ctx=work_ctx, **match_attrs
    )
