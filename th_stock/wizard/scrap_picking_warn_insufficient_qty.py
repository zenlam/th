from odoo import models, fields, api, _


class ScrapPickingWarnInsufficientQty(models.TransientModel):
    _name = 'scrap.picking.warn.insufficient.qty'
    _description = 'TH Warn Insufficient Scrap Quantity'

    scrap_picking_id = fields.Many2one('scrap.picking', string='Scrap Picking',
                                       required=True)
    location_id = fields.Many2one('stock.location', string='Location',
                                  required=True)
    scrap_ids = fields.Many2many('stock.scrap',
                                 compute='_compute_scrap_ids')

    @api.depends('scrap_picking_id')
    def _compute_scrap_ids(self):
        force_scrap_ids = self._context.get('force_scrap_id')
        scraps = self.env['stock.scrap'].search([
            ('id', 'in', force_scrap_ids)
        ])
        self.scrap_ids = scraps

    def action_done(self):
        for scrap in self.scrap_picking_id.stock_scrap_ids:
            scrap.do_scrap()
        self.scrap_picking_id.write({'state': 'done'})
