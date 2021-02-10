from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class ScrapPicking(models.Model):
    _name = 'scrap.picking'
    _description = 'TH Scrap Picking'

    def _get_default_scrap_location_id(self):
        stock_location_obj = self.env['stock.location']
        return stock_location_obj.search([
            ('scrap_location', '=', True),
            ('company_id', 'in', [self.env.user.company_id.id, False])
        ], limit=1).id

    name = fields.Char(string='Name', default=_('New'),
                       copy=False, readonly=True)
    date = fields.Datetime(string='Date', default=datetime.now())
    outlet_id = fields.Many2one('stock.warehouse', string='Outlet',
                                domain=[('is_outlet', '=', True)])
    source_loc_id = fields.Many2one('stock.location',
                                    string='Source Location')
    damage_loc_id = fields.Many2one('stock.location',
                                    string='Damage Location',
                                    domain=[('scrap_location', '=', True)],
                                    default=_get_default_scrap_location_id)
    analytic_account_id = fields.Many2one('account.analytic.account',
                                          string='Analytic Account',
                                          required=1)
    remark = fields.Text(string='Remark')
    origin = fields.Char(string='Source Document')
    damage_reason_id = fields.Many2one('damage.reason', string='Damage Reason',
                                       domain=[('active', '=', True)])
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)
    scrap_line_ids = fields.One2many('scrap.picking.line', 'scrap_picking_id',
                                     string='Scrap Product')
    stock_scrap_ids = fields.One2many('stock.scrap', 'scrap_picking_id',
                                      string='Scrap Details')
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('submit', 'To Approve'),
                   ('done', 'Done'), ('cancel', 'Cancel')],
        string='Status', default='draft'
    )

    def action_get_stock_move_lines(self):
        return {
            'name': _('Product Moves'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.move.line',
            'target': 'current',
            'domain': [('scrap_picking_id', '=', self.id)],
        }

    @api.model
    def _get_lot_dict(self, qty, location_id, product_id):
        lot_dict = {}
        quants = self.env['stock.quant'].search([
            ('location_id', '=', location_id),
            ('product_id', '=', product_id)
        ]).sorted(key=lambda s: s.lot_id.removal_date)
        temp_qty = qty
        for quant in quants:
            if temp_qty > 0:
                avail_qty = quant.quantity - quant.reserved_quantity
                scrap_qty = min(avail_qty, temp_qty)
                temp_qty -= scrap_qty
                lot_dict[quant.lot_id.id] = scrap_qty
            else:
                break
        if temp_qty > 0:
            lot_name = 'Negative Quantity'
            new_lot_id = self.env['stock.production.lot'].search([
                ('name', '=', lot_name),
                ('product_id', '=', product_id)
            ], limit=1)
            if not new_lot_id:
                lot_vals = {
                    'product_id': product_id,
                    'name': lot_name,
                    'removal_date': datetime.now()
                }
                new_lot_id = self.env['stock.production.lot'].create(lot_vals)
            lot_dict[new_lot_id.id] = temp_qty
        return lot_dict

    @api.model
    def _prepare_stock_scrap_values(self, line):
        vals_list = []
        fix_vals = {
            'location_id': line.scrap_picking_id.source_loc_id.id,
            'scrap_location_id': line.scrap_picking_id.damage_loc_id.id,
            'account_analytic_id':
                line.scrap_picking_id.analytic_account_id.id,
            'origin': line.scrap_picking_id.name,
            'date_expected': line.scrap_picking_id.date,
            'scrap_picking_id': line.scrap_picking_id.id,
        }
        if line.menu_id:
            for prod_id in line.menu_id.product_ingredient_ids:
                if prod_id.product_id.tracking != 'none':
                    lot_dict = self._get_lot_dict(
                        line.quantity,
                        line.scrap_picking_id.source_loc_id.id,
                        prod_id.product_id.id)
                    for lot in lot_dict:
                        vals = {
                            'menu_id': line.menu_id.id,
                            'product_id': prod_id.product_id.id,
                            'scrap_qty': lot_dict[lot],
                            'lot_id': lot,
                            'product_uom_id': line.product_uom.id,
                        }
                        vals.update(fix_vals)
                        vals_list.append(vals)
                else:
                    vals = {
                        'menu_id': line.menu_id.id,
                        'product_id': prod_id.product_id.id,
                        'scrap_qty': (prod_id.qty * line.quantity),
                        'product_uom_id': prod_id.uom_id.id
                    }
                    vals.update(fix_vals)
                    vals_list.append(vals)
        elif line.ingredient_id:
            if line.ingredient_id.tracking != 'none':
                lot_dict = self._get_lot_dict(
                    line.quantity,
                    line.scrap_picking_id.source_loc_id.id,
                    line.ingredient_id.id)
                for lot in lot_dict:
                    vals = {
                        'product_id': line.ingredient_id.id,
                        'scrap_qty': lot_dict[lot],
                        'lot_id': lot,
                        'product_uom_id': line.product_uom.id,
                    }
                    vals.update(fix_vals)
                    vals_list.append(vals)
            else:
                vals = {
                    'product_id': line.ingredient_id.id,
                    'scrap_qty': line.quantity,
                    'product_uom_id': line.product_uom.id,
                }
                vals.update(fix_vals)
                vals_list.append(vals)
        return vals_list

    @api.model
    def generate_scrap_details(self):
        stock_scrap_obj = self.env['stock.scrap']
        self.stock_scrap_ids.sudo().unlink()
        for line in self.scrap_line_ids:
            line_vals = self._prepare_stock_scrap_values(line)
            for vals in line_vals:
                stock_scrap_obj.create(vals)

    def button_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancel'})

    def button_validate(self):
        self.ensure_one()
        force_scrap_ids = []
        view = self.env.ref(
            'th_stock.scrap_picking_warn_insufficient_qty_view_form').id
        for line in self.stock_scrap_ids:
            precision = self.env['decimal.precision'].precision_get(
                'Product Unit of Measure')
            available_qty = sum(self.env['stock.quant']._gather(
                line.product_id,
                line.location_id,
                line.lot_id,
                line.package_id,
                line.owner_id,
                strict=True).mapped('quantity'))
            scrap_qty = line.product_uom_id._compute_quantity(
                line.scrap_qty, line.product_id.uom_id)
            if float_compare(available_qty, scrap_qty,
                             precision_digits=precision) < 0:
                force_scrap_ids.append(line.id)
        if force_scrap_ids:
            return {
                'name': _('Insufficient Quantity'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'scrap.picking.warn.insufficient.qty',
                'view_id': view,
                'type': 'ir.actions.act_window',
                'context': {
                    'default_scrap_picking_id': self.id,
                    'default_location_id': self.source_loc_id.id,
                    'force_scrap_id': force_scrap_ids,
                },
                'target': 'new'
            }
        else:
            for line in self.stock_scrap_ids:
                line.do_scrap()
            self.write({'state': 'done'})

    def button_submit(self):
        self.ensure_one()
        if not self.scrap_line_ids:
            raise ValidationError(_('There must be at least one product '
                                    'configured to do the transfer.'))
        self.write({'state': 'submit'})

    @api.onchange('outlet_id')
    def onchange_outlet_id(self):
        if self.outlet_id:
            self.source_loc_id = self.outlet_id.lot_stock_id.id
            self.analytic_account_id = \
                self.outlet_id.lot_stock_id.account_analytic_id.id

    def unlink(self):
        if 'done' in self.mapped('state'):
            raise UserError(_('You cannot delete a scrap which is done.'))
        return super(ScrapPicking, self).unlink()

    @api.multi
    def write(self, vals):
        res = super(ScrapPicking, self).write(vals)
        if vals.get('scrap_line_ids', False):
            self.generate_scrap_details()
        return res

    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = \
                self.env['ir.sequence'].next_by_code('scrap.picking') or 'New'
        res = super(ScrapPicking, self).create(vals)
        if res.scrap_line_ids:
            res.generate_scrap_details()
        return res
