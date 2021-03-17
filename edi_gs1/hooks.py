# Copyright 2021 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.api import SUPERUSER_ID, Environment


def post_init_hook(cr, registry):
    """
    Hook used to init automatically some GS1 code on existing UoM
    :param cr: database cursor
    :param registry:
    :return:
    """
    env = Environment(cr, SUPERUSER_ID, {"tracking_disable": True})
    env["uom.uom"]._execute_gs1_map_code()
