# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class BaseEDIExchange (models.Model):
    _inherit = 'base.edi.exchange'

    type = fields.Selection(selection_add=[('sftp', _('SFTP'))])
