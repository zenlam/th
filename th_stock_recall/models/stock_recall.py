# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import fields, api, models, _


class StockRecall(models.Model):
    _name = 'stock.recall'
    _inherit = ['mail.thread']

    @api.multi
    @api.depends('picking_ids')
    def _compute_picking_count(self):
        """

        :return:
        """
        for r in self:
            r.picking_count = len(r.picking_ids.ids)

    name = fields.Char(string=_('Number'))
    reason_id = fields.Many2one(comodel_name='stock.recall.reason', string=_('Reason of Recall'), required=True,
                                readonly=True, states={'draft': [('readonly', False)]})
    date_create = fields.Date(string=_('Creation Date'),
                              default=lambda self: fields.Date.context_today(self, fields.Datetime.now()),
                              readonly=True)
    create_uid = fields.Many2one(comodel_name='res.users', string=_('Created By'),
                                 default=lambda self: self.env.user, readonly=True)
    remark = fields.Text(string=_('Remark'))
    outlet_ids = fields.Many2many(comodel_name='stock.warehouse', domain=[('create_from', '=', 'outlet')],
                                  relation='stock_recall_outlet_rel', column1='recall_id', column2='outlet_id',
                                  string=_('Outlets'), readonly=True, states={'draft': [('readonly', False)]})
    all_outlet = fields.Boolean(string=_('All Outlets'), readonly=True, states={'draft': [('readonly', False)]})
    product_ids = fields.One2many(comodel_name='stock.recall.product', inverse_name='recall_id',
                                  string=_('Products'), readonly=True, states={'draft': [('readonly', False)]})
    picking_ids = fields.One2many(comodel_name='stock.picking', inverse_name='recall_id',
                                  string=_('Pickings'), readonly=True)
    picking_count = fields.Integer(string='Picking Count', compute='_compute_picking_count')
    state = fields.Selection(selection=[('draft', _('Draft')),
                                        ('pending', _('Pending')),
                                        ('done', _('Done')),
                                        ('cancelled', _('Cancelled'))],
                             string=_('Status'), default='draft', track_visibility='always')

    def _prepare_recall_picking_vals(self, outlet, origin=False):
        return {
            'location_id': outlet.lot_stock_id.id,
            'location_dest_id': self.env['stock.warehouse'].search([('is_hq', '=', True)], limit=1).lot_stock_id.id,
            'picking_type_id': outlet.int_type_id.id,
            'origin': origin,
            'recall_id': self.id,
            'note': self.reason_id.description
        }

    def _prepare_recall_move_vals(self, product, picking):
        return {
            'picking_id': picking.id,
            'product_id': product.product_id.id,
            'product_uom': product.uom_id.id,
            # if you prefer to recall all qty in outlet stock, just un-comment line below and remove 'product_uom_qty': 0
            # 'product_uom_qty': product.product_id.with_context(location=picking.location_id.id, lot_id=product.lot_id.id if product.lot_id.id else None).qty_available,
            'product_uom_qty': 0,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'recall_line_id': product.id,
            'name': '/'
        }

    def _generate_recall_picking_for(self, outlet, origin=False):
        """

        :param outlet:
        :return:
        """
        return self.env['stock.picking'].create(self._prepare_recall_picking_vals(outlet))

    def _generate_recall_moves(self, picking):
        """

        :param picking:
        :return:
        """
        MoveModel = moves = self.env['stock.move']
        for product in self.product_ids:
            moves |= MoveModel.create(self._prepare_recall_move_vals(product, picking))
        return moves

    @api.multi
    def button_generate_pickings(self):
        """

        :return:
        """
        self.ensure_one()
        name = self.env.ref('th_stock_recall.th_stock_recall_sequence').next_by_id()
        if self.all_outlet:
            outlets = self.env['stock.warehouse'].search([('create_from', '=', 'outlet')])
        else:
            outlets = self.outlet_ids
        for outlet in outlets:
            picking = self._generate_recall_picking_for(outlet=outlet, origin=name)
            moves = self._generate_recall_moves(picking)
        self.write({'state': 'pending',
                    'name': name})

    @api.multi
    def button_cancel(self):
        """

        :return:
        """
        for p in self.picking_ids:
            if p.state != 'cancel':
                p.action_cancel()
        return self.write({'state': 'cancelled'})

    @api.multi
    def button_setto_draft(self):
        """

        :return:
        """
        return self.write({'state': 'draft'})

    @api.multi
    def action_done(self):
        """

        :return:
        """
        return self.write({'state': 'done'})

    @api.multi
    def button_view_pickings(self):
        """

        :return:
        """
        return {
            'type': 'ir.actions.act_window',
            'name': _('Recall Picking'),
            'res_model': 'stock.picking',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('id', 'in', self.picking_ids.ids)]
        }


class StockRecallProduct(models.Model):
    _name = 'stock.recall.product'

    recall_id = fields.Many2one(comodel_name='stock.recall', string=_('Recall'))
    product_id = fields.Many2one(comodel_name='product.product', string=_('Product'), required=True)
    lot_id = fields.Many2one(comodel_name='stock.production.lot', string=_('Lot number'))
    life_date = fields.Datetime(string=_('Expiry date'), related='lot_id.life_date')
    uom_id = fields.Many2one(comodel_name='uom.uom', string=_('Recall UOM'))
    qty_received_recall = fields.Float(string=_('Received Recall Qty'), readonly=True)
