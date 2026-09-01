# Copyright 2026 bosd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Populate the new m2m keyword pool from the renamed Text columns.

Reads ``keywords_text_deprecated`` / ``exclude_keywords_text_deprecated``
(one keyword per non-empty line) that ``pre-migration.py`` preserved,
creates ``invoice2data.template.keyword`` records de-duplicating on name,
and populates the two m2m relation tables (``..._keyword_rel`` for
inclusion, ``..._exclude_keyword_rel`` for exclusion).

Finally drops the deprecated columns so subsequent upgrades don't see
stale data.
"""

import logging

_logger = logging.getLogger(__name__)


def _iter_lines(blob):
    """Split a Text column blob into stripped non-empty lines."""
    if not blob:
        return
    for line in blob.splitlines():
        stripped = line.strip()
        if stripped:
            yield stripped


def _ensure_keyword(env, cache, name):
    """Return the id of the keyword record for ``name``, creating if needed."""
    if name in cache:
        return cache[name]
    Keyword = env["invoice2data.template.keyword"].sudo()
    existing = Keyword.search([("name", "=", name)], limit=1)
    if existing:
        cache[name] = existing.id
    else:
        cache[name] = Keyword.create({"name": name}).id
    return cache[name]


def migrate(cr, version):
    if not version:
        return
    from odoo import api, SUPERUSER_ID

    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute("""
        SELECT id, keywords_text_deprecated, exclude_keywords_text_deprecated
        FROM invoice2data_template
        """)
    rows = cr.fetchall()
    cache = {}
    total_kw = total_ex = 0
    for tpl_id, kw_text, ex_text in rows:
        for name in _iter_lines(kw_text):
            kw_id = _ensure_keyword(env, cache, name)
            cr.execute(
                """
                INSERT INTO invoice2data_template_keyword_rel
                    (template_id, keyword_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (tpl_id, kw_id),
            )
            total_kw += 1
        for name in _iter_lines(ex_text):
            kw_id = _ensure_keyword(env, cache, name)
            cr.execute(
                """
                INSERT INTO invoice2data_template_exclude_keyword_rel
                    (template_id, keyword_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (tpl_id, kw_id),
            )
            total_ex += 1
    cr.execute("ALTER TABLE invoice2data_template DROP COLUMN keywords_text_deprecated")
    cr.execute(
        "ALTER TABLE invoice2data_template DROP COLUMN exclude_keywords_text_deprecated"
    )
    _logger.info(
        "invoice2data_template: migrated %d rows -> %d keyword links, "
        "%d exclude-keyword links; %d unique keywords",
        len(rows),
        total_kw,
        total_ex,
        len(cache),
    )
