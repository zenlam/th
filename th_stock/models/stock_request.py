from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockRequest(models.Model):
    _inherit = "stock.picking"

    is_stock_transfer = fields.Boolean(string="Is Stock Transfer",
                                       default=False)
    show_approve = fields.Boolean(string="Show Approve Button", readonly=True)
    requested_outlet = fields.Many2one('stock.warehouse',
                                       string="Requested Outlet")
    sender_outlet = fields.Many2one('stock.warehouse', string="Sender Outlet")
    approve_by = fields.Many2one('res.users', string="Approved By",
                                 readonly=True)

    # @api.multi
    # def button_validate(self):
    #     if self.is_stock_transfer:
    #         lines_to_check = self.move_line_ids
    #         for line in lines_to_check:
    #             product = line.product_id
    #             if product and product.tracking != 'none':
    #                 if not line.stock_request_lot_id:
    #                     raise UserError(_('You need to supply a Lot/Serial '
    #                                       'number for product %s.'
    #                                       ) % product.display_name)
    #     return super(StockRequest, self).button_validate()

    @api.multi
    @api.depends('create_uid')
    def _compute_show_approve(self):
        for picking in self:
            if picking.create_uid.id == self.env.context.get('uid'):
                picking.show_approve = False
            else:
                picking.show_approve = True

    @api.multi
    def action_sender_approve(self):
        self.approve_by = self._uid
        self.state = 'approve'

    @api.multi
    def action_submit(self):
        self.state = 'pending'

    @api.model
    def create(self, vals):
        if 'is_stock_transfer' in vals and vals['is_stock_transfer'] is True:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'stock.transfer') or '/'

        if vals.get('sender_outlet', False):
            sender_id = self.env['stock.warehouse'].search([
                ('id', '=', vals['sender_outlet'])
            ])
            vals['location_id'] = self.env['stock.location'].search([
                ('id', '=', sender_id.lot_stock_id.id)
            ]).id
        if vals.get('requested_outlet', False):
            requester_id = self.env['stock.warehouse'].search([
                ('id', '=', vals['requested_outlet'])
            ])
            vals['location_dest_id'] = self.env['stock.location'].search([
                ('id', '=', requester_id.lot_stock_id.id)
            ]).id
        return super(StockRequest, self).create(vals)

    @api.onchange('requested_outlet', 'sender_outlet')
    def get_src_dest_loc(self):
        if self.requested_outlet:
            self.location_dest_id = self.env['stock.location'].search([
                ('id', '=', self.requested_outlet.lot_stock_id.id)
            ])
        else:
            self.location_dest_id = False
        if self.sender_outlet:
            self.location_id = self.env['stock.location'].search([
                ('id', '=', self.sender_outlet.lot_stock_id.id)
            ])
        else:
            self.location_id = False
