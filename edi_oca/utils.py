# Copyright 2020 ACSONE SA
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import hashlib

from odoo.addons.http_routing.models.ir_http import slugify
from odoo.addons.queue_job.job import identity_exact_hasher


def normalize_string(a_string, sep="_"):
    """Normalize given string, replace dashes with given separator."""
    return slugify(a_string).replace("-", sep)


def get_checksum(filecontent):
    return hashlib.md5(filecontent).hexdigest()


def exchange_record_job_identity_exact(job_):
    hasher = identity_exact_hasher(job_)
    # Include files checksum
    hasher.update(
        str(sorted(job_.recordset.mapped("exchange_filechecksum"))).encode("utf-8")
    )
    return hasher.hexdigest()
