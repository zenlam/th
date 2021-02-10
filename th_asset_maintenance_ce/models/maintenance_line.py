# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MaintenanceLine(models.Model):
    _name = 'custom.maintenance.line'

    line_type = fields.Selection([
        ('purchase', 'Purchase Order'),
        ('internal', 'Internal Transfer')],
        default='purchase',
        required=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
    )
    price = fields.Float(
        string='Price',
        required=True,
    )
    uom_id = fields.Many2one(
        'uom.uom',#product.uom
        string='Uom',
        required=True,
    )
    quantity = fields.Float(
        string='Quantity',
        required=True,
    )
    custom_description = fields.Char(
        string='Description',
        required=True,
    )
    maintenance_id = fields.Many2one(
        'maintenance.request',
        string='Maintenance',
        required=True,
    )
    partner_id = fields.Many2many(
        'res.partner',
        string='Vendors',
    )
    sub_total = fields.Float(
        string="Sub Total",
        compute="_compute_sub_total",
        store=True,
    )
    old_qty = fields.Float(
        string="Old Quantity",
        store=True,
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            rec.custom_description = rec.product_id.name
            rec.uom_id = rec.product_id.uom_id.id
            rec.quantity = 1
            rec.price = rec.product_id.lst_price
    
    @api.depends('quantity', 'price')
    def _compute_sub_total(self):
        for rec in self:
            rec.sub_total = rec.price * rec.quantity

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
