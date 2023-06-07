# Copyright 2021 ForgeFlow <http://www.forgeflow.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Create existing related record instances.")
    cr.execute(
        """
        WITH query AS (
            SELECT id, model, res_id
            FROM edi_exchange_record
            WHERE model IS NOT NULL
        )
        INSERT INTO edi_exchange_related_record (exchange_record_id, model, res_id)
        SELECT * FROM query;
    """
    )
