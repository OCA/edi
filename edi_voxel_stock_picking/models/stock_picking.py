# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, exceptions, models


class Picking(models.Model):
    _name = "stock.picking"
    _inherit = ['stock.picking', 'voxel.mixin']

    voxel_enabled = fields.Boolean(related='company_id.voxel_enabled')
    voxel_job_ids = fields.Many2many(
        comodel_name="queue.job",
        relation="stock_picking_voxel_job_rel",
        column1="picking_id",
        column2="voxel_job_id",
        string="Jobs", copy=False)

    @api.multi
    def action_done(self):
        res = super(Picking, self).action_done()
        for picking in self.filtered(
                lambda p: p.picking_type_code == 'outgoing'):
            picking.action_send_to_voxel()
        return res

    @api.multi
    def action_cancel(self):
        jobs = self.mapped('voxel_job_ids')
        if not self._cancel_voxel_jobs(jobs):
            raise exceptions.Warning(_(
                'You can not cancel this delivery order because'
                ' there is a job running!'))
        return super(Picking, self).action_cancel()

    @api.multi
    def action_send_to_voxel(self):
        # Check if it is a return picking
        def able_to_voxel(record):
            enabled = record.company_id.voxel_enabled
            type_code = record.picking_type_code
            is_outgoing = type_code == 'outgoing'
            is_incoming_returned = (type_code == 'incoming' and bool(
                record.move_lines.mapped('origin_returned_move_id')))
            return enabled and (is_outgoing or is_incoming_returned)

        pickings = self.filtered(able_to_voxel)
        if pickings:
            pickings.enqueue_voxel_report(
                'edi_voxel_stock_picking.report_voxel_picking')

    @api.multi
    def get_document_type(self):
        """ Document type name to be used in the name of the Voxel report"""
        return "Albaran"
