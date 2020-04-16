# -*- coding: utf-8 -*-
# © 2020 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from openerp import api, models
from openerp.tools.misc import file_open

logger = logging.getLogger(__name__)


class InventoryUblHelper(models.TransientModel):
    _name = "inventory.ubl.helper"

    _description = "Inventory Report Helper for test and demo"

    @api.multi
    def _import_main_xml_file_when_demo_and_test(self):
        wizard = self.env["inventory.ubl.helper"]._create_inventory_transient("main")
        wizard.process_document()
        logger.info("'main.xml' file has been imported.")

    @api.model
    def _create_inventory_transient(self, file_name):
        FILE_PATH = "supplier_inventory_import_ubl/tests/inventory_report_sample"
        with file_open("%s/%s.xml" % (FILE_PATH, file_name), "rb") as f:
            self.inventory_xml = f.read()
            return self.env["inventory.ubl.import"].create(
                {"document": self.inventory_xml.encode("base64")}
            )
