# Copyright 2026 Camptocamp SA (https://camptocamp.com/)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Migrate data from version < 18.0

    Data to migrate:
        - rename PO field ``supplier_ack_dt`` to ``supplier_ack_received_on``
        - rename PO response menu, action and form view XMLIDs
    """
    openupgrade.rename_fields(
        env,
        field_spec=[
            (
                "purchase.order",
                "purchase_order",
                "supplier_ack_dt",
                "supplier_ack_received_on",
            ),
        ],
    )
    openupgrade.rename_xmlids(
        env.cr,
        xmlids_spec=[
            (
                "purchase_order_import.order_response_import_form",
                "purchase_order_import.purchase_order_response_import_form",
            ),
            (
                "purchase_order_import.order_response_import_action",
                "purchase_order_import.purchase_order_response_import_action",
            ),
            (
                "purchase_order_import.order_response_import_importer_menu",
                "purchase_order_import.purchase_order_response_import_importer_menu",
            ),
        ],
    )
