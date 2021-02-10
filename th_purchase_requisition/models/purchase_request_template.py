# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError

class PurchaseRequestTemplate(models.Model):
    _name = "purchase.request.tmpl"

    name = fields.Char('Template Name', required=True)
    partner_id = fields.Many2one('res.partner', domain="[('supplier','=',True)]", required=True)
    start_date = fields.Date('Start Date Validity', required=True)
    end_date = fields.Date('End Date Validity', required=True)
    vendor_lead_time = fields.Integer('Vendor Lead Time(days)')
    purchase_request_tmpl_line_ids = fields.One2many('purchase.request.tmpl.line', 'purchase_request_tmpl_id', string="Products")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    outlet_ids = fields.Many2many('stock.warehouse', compute='_compute_outlets', search='_search_outlets', string='Outlet(s)', store=False)

    @api.depends('purchase_request_tmpl_line_ids','purchase_request_tmpl_line_ids.outlet_ids')
    def _compute_outlets(self):
        for record in self:
            outlets = self.env['stock.warehouse']
            for line in record.purchase_request_tmpl_line_ids:
                outlets |= line.outlet_ids
            record.outlet_ids = outlets

    @api.model
    def _search_outlets(self, operator, operand):
        outlets = self.env['stock.warehouse']
        req_ids = []
        if operator == 'child_of':
            for record in self.search([]):
                for line in record.purchase_request_tmpl_line_ids:
                    if line.outlet_ids.filtered(lambda x: x.id in operand):
                        req_ids.append(record.id)
        return [('id','in', req_ids)]

    @api.constrains('partner_id','start_date','end_date')
    def _check_unique_vendor_with_period(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError(_('Template start date must be earlier than contract end date.'))
        if self.partner_id and self.start_date and self.end_date:
            records = self.search([ '&',
                                    ('id','!=',self.id),
                                    '&',
                                    ('partner_id','=',self.partner_id.id),
                                    '|',
                                    '|',
                                    '|',

                                    '&',
                                    '&',('start_date','>=',self.start_date),('start_date','<=',self.end_date),
                                    '&',('end_date','>=',self.start_date),('end_date','>=',self.end_date),

                                    '&',
                                    '&',('start_date','<=',self.start_date),('start_date','<=',self.end_date),
                                    '&',('end_date','>=',self.start_date),('end_date','<=',self.end_date),

                                    '&',
                                    '&',('start_date','<=',self.start_date),('start_date','<=',self.end_date),
                                    '&',('end_date','>=',self.start_date),('end_date','>=',self.end_date),

                                    '&',
                                    '&',('start_date','>=',self.start_date),('start_date','<=',self.end_date),
                                    '&',('end_date','>=',self.start_date),('end_date','<=',self.end_date)
                                ])
            if records:
                raise ValidationError("Purchase request template should be only one per vendor for same dates period !")



class PurchaseRequestTemplateLine(models.Model):
    _name = "purchase.request.tmpl.line"

    purchase_request_tmpl_id = fields.Many2one('purchase.request.tmpl', string='Request Template')
    product_ids = fields.Many2many('product.product', 'pur_req_tmpl_line_product_rel', string='Products', domain=[('direct_order_to_spplier','=',True)], required=True)
    requisition_tmpl_id = fields.Many2one('purchase.requisition.template', string='Sales History Template', required=True)
    outlet_ids = fields.Many2many('stock.warehouse', 'pur_req_tmpl_line_outlet_rel', domain=[('is_outlet','=',True)], string='Outlet(s)')
    area_id = fields.Many2one('res.country.area', string="Outlet Based on Area")

    @api.multi
    def filter_tmpl_lines(self, outlet):
        """ This method return the filtered lines based on outlet argument.
            because template lines are too flexible [ No validation for uniqueness in terms of product according to outlet/area ]
        """
        filtered_lines = self.env['purchase.request.tmpl.line']
        for line in self:
            if outlet.id in line.outlet_ids.ids or outlet.area_id.id == line.area_id.id:
                filtered_lines |= line
        return filtered_lines



