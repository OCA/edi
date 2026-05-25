# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """The format of dates and datetimes is changed to a new char field
    The goal is to avoid a drop-down menu with all possible format options,
    thereby achieving much greater flexibility by specifying the format as text.

    It will be changed (date_format):
    *Y-*d-*m: %Y-%d-%m
    *m-*d-*Y: %m-%d-%Y
    *d-*m-*Y: %d-%m-%Y
    *Y/*d/*m: %Y/%d/%m
    *m/*d/*Y: %m/%d/%Y
    *d.*m.*Y: %d.%m.%Y
    *d.*m.*y-short: %d.%m.%y
    *d/*m/*Y: %d/%m/%Y
    *d/*m/*y-short: %d/%m/%y
    *B *d, *Y: %B %d, %Y
    *b-short *d, *Y: %b %d, %Y
    *d *b-short *Y: %d %b %Y
    *d *B *Y: %d %B %Y
    *d-*b-*y: %d-%b-%y
    *d-*b-short-*Y: %d-%b-%Y

    It will be changed (time_format):
    *H:*M:*S: %H:%M:%S

    Other custom formats added to the selection fields will also be considered, taking
    into account (*) and (-short)
    """
    openupgrade.logged_query(
        env.cr,
        """
         ALTER TABLE base_import_pdf_template_line
         ADD COLUMN IF NOT EXISTS date_time_format VARCHAR
         """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE base_import_pdf_template_line biptl
        SET date_time_format =
            replace(replace(biptl.date_format, '*', '%'), '-short', '')
            ||
            CASE
                WHEN imf.ttype = 'datetime'
                THEN ' ' || replace(biptl.time_format, '*', '%')
                ELSE ''
            END
        FROM ir_model_fields imf
        WHERE biptl.field_id = imf.id
        AND biptl.date_format IS NOT NULL;
        """,
    )
