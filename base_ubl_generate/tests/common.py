# Copyright 2025 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import random


class DummyRecord:
    """Minimal dummy object for partner, company, product, etc.

    This module can be used without a full Odoo environment,
    simulating the necessary attributes and methods.

    This way we can test handling line items w/o depending on ``product``
    or other Odoo modules.
    """

    def __init__(self, model=None, **kwargs):
        self.__dict__.update(kwargs)
        self.id = random.randint(1, 1000)  # Simulate an ID for the dummy object
        self._ids = [self.id]

    def __iter__(self):
        yield from self._iter

    def __getattr__(self, item):
        return None

    def __repr__(self):
        if hasattr(self, "name"):
            name = self.name
        else:
            name = f"{self.__dict__}"
        return f"<DummyRecord: {name}>"
