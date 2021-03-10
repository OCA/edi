# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.http_routing.models.ir_http import slugify


def normalize_string(a_string, sep="_"):
    """Normalize given string, replace dashes with given separator."""
    return slugify(a_string).replace("-", sep)
