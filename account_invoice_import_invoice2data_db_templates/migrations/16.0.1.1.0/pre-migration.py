# Copyright 2026 bosd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Rename the old Text keyword columns so post-migration can read them.

The 16.0.1.1.0 upgrade converts ``keywords`` and ``exclude_keywords`` on
``invoice2data.template`` from ``fields.Text`` (newline-separated) to
``fields.Many2many`` pointing at a shared ``invoice2data.template.keyword``
pool. Odoo's ORM would otherwise drop the old columns before the field
type change (there's no in-place TEXT -> many2many conversion), so we
rename them here and copy their content in ``post-migration``.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        # Fresh install; nothing to migrate.
        return
    cr.execute(
        """
        ALTER TABLE invoice2data_template
        RENAME COLUMN keywords TO keywords_text_deprecated
        """
    )
    cr.execute(
        """
        ALTER TABLE invoice2data_template
        RENAME COLUMN exclude_keywords TO exclude_keywords_text_deprecated
        """
    )
    _logger.info(
        "invoice2data_template: renamed Text keyword columns for m2m migration"
    )
