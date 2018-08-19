# -*- coding: utf-8 -*-
# Copyright 2018 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

logger = logging.getLogger(__name__)
try:
    from weboob.core import Weboob
    from weboob.exceptions import ModuleInstallError
except ImportError:
    logger.debug('Cannot import weboob')


class WeboobModule(models.Model):
    _name = 'weboob.module'
    _description = 'Weboob module for account_invoice_download framework'

    name = fields.Char(readonly=True, required=True)
    active = fields.Boolean(default=True)
    maintainer = fields.Char(readonly=True)
    installed_version = fields.Char(string='Installed Version', readonly=True)
    available_version = fields.Char(string='Available Version', readonly=True)
    license = fields.Char(readonly=True)
    description = fields.Char(readonly=True)
    has_parameters = fields.Boolean(
        string='Has Additional Parameters', readonly=True)
    state = fields.Selection([
        ('uninstalled', 'Not Installed'),
        ('installed', 'Installed'),
        ], default='uninstalled', string='State', required=True, readonly=True)

    @api.depends('name', 'description')
    def name_get(self):
        res = []
        for rec in self:
            name = rec.name
            if rec.description:
                name = '%s (%s)' % (rec.description, name)
            res.append((rec.id, name))
        return res

    @api.model
    def update_module_list(self):
        w = Weboob()
        logger.info('Weboob: calling update_repositories')
        w.repositories.update_repositories()
        weboob_modules = w.repositories.get_all_modules_info('CapDocument')
        module_name2obj = {}
        for module in self.search_read([], ['name']):
            module_name2obj[module['name']] = self.browse(module['id'])
        for name, info in weboob_modules.iteritems():
            vals = {
                'name': name,
                'maintainer': info.maintainer,
                'license': info.license,
                'description': info.description,
                'available_version': info.version,
                'state': 'uninstalled',
                }
            if info.is_installed():
                vals.update({
                    'has_parameters': self.has_parameter(w, name),
                    'state': 'installed',
                    'installed_version': info.version,
                    })
            if name in module_name2obj:
                module_name2obj[name].write(vals)
            else:
                self.create(vals)

    @api.model
    def has_parameter(self, w, module_name):
        bmod = w.modules_loader.get_or_load_module(module_name)
        has_parameter = False
        for key, value in bmod.config.iteritems():
            if key not in ['login', 'password']:
                has_parameter = True
                break
        logger.debug('module %s has_parameter=%s', module_name, has_parameter)
        return has_parameter

    def get_installed_version(self, w):
        self.ensure_one()
        weboob_module = w.repositories.get_module_info(self.name)
        version = weboob_module.get('version')
        return version

    def install(self):
        w = Weboob()
        for module in self:
            if module.state == 'uninstalled':
                logger.info(
                    'Starting to install weboob module %s', module.name)
                w.repositories.install(module.name)
                has_parameter = self.has_parameter(w, module.name)
                module.write({
                    'state': 'installed',
                    'installed_version': module.available_version,
                    'has_parameter': has_parameter,
                    })
                logger.info('Weboob module %s is now installed', module.name)

    def upgrade(self):
        w = Weboob()
        logger.info('Weboob: calling update_repositories')
        w.repositories.update_repositories()
        for module in self:
            if module.state == 'installed':
                # it seems that you must call install to update a module!
                logger.info('Starting to upgrade module %s', module.name)
                try:
                    w.repositories.install(module.name)
                except ModuleInstallError as e:
                    raise UserError(_(
                        "Error when upgrading module '%s'. Error message: %s.")
                        % (module.name, e))
                new_version = module.get_installed_version(w)
                logger.info(
                    'Weboob module %s has been updated from version %s to %s',
                    module.name, module.installed_version,
                    new_version)
                module.write({
                    'installed_version': new_version,
                    'available_version': new_version,
                    })
