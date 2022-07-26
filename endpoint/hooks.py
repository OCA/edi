# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

from odoo import SUPERUSER_ID, api, tools

from odoo.addons.base.models.ir_model import query_insert

_logger = logging.getLogger(__file__)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _init_server_action(env)


def _init_server_action(env):
    """Create server action if missing."""
    # This is actually a trick to work around this error:
    #
    #   psycopg2.IntegrityError: null value in column "activity_user_type"
    #   violates not-null constraint
    #
    # which happens when `mail` is installed,
    # since it adds this field as required in DB.
    #
    # We DO NOT want to depend on mail for this problem...
    # hence, here we go with this crazy dance :S
    #
    # Moreover, we are forced to use a query for this
    # because if you use `model.create` you get
    #
    #   ValueError: Invalid field 'activity_user_type' on model 'ir.actions.server'
    #
    # because the field is not yet in the env if the mail modules is not loaded 1st.
    xid = "endpoint.server_action_registry_sync"
    rec = env.ref(xid, False)
    if rec:
        return
    model = env.ref("endpoint.model_endpoint_endpoint")
    values = {
        "name": "Sync registry",
        "type": "ir.actions.server",
        "model_id": model.id,
        "model_name": model.model,
        "binding_model_id": model.id,
        "binding_type": "action",
        "usage": "ir_actions_server",
        "state": "code",
        "code": """
records.filtered(lambda x: not x.registry_sync).write({"registry_sync": True})
""",
    }
    if tools.sql.column_exists(env.cr, "ir_act_server", "activity_user_type"):
        values["activity_user_type"] = "specific"
    ids = query_insert(
        env.cr,
        "ir_act_server",
        [
            values,
        ],
    )

    # Finally add an xmlid
    module, id_ = xid.split(".", 1)
    env["ir.model.data"].create(
        {
            "name": id_,
            "module": module,
            "model": "ir.actions.server",
            "res_id": ids[0],
            "noupdate": True,
        }
    )
    _logger.info("Server action created")
