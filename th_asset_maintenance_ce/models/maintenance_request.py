# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    is_asset_maintenance = fields.Boolean(
        string="Is Asset Maintenance"
    )

#    @api.multi
#    @api.depends('estimate_completion_days', 'stage_id')
#    def _estimate_completion_date(self):
#        for rec in self:
#            print ("----------------------",rec.estimate_completion_date)
#            if rec.stage_id.state == 'submit':
#                print ("----------------------",rec.estimate_completion_date)
#                rec.estimate_completion_date = datetime.today() + relativedelta(days=+rec.estimate_completion_days)
#            else:
#                rec.estimate_completion_date = rec.estimate_completion_date
#            print ("------------==========",rec.estimate_completion_date)

#    @api.multi
#    @api.depends('request_date', 'stage_id')
#    def _days_not_acted(self):
#        for rec in self:
#            print ("&&&&&&&&&&&&&&^&^^^^^^^^^^^^^",rec.days_not_acted)
#            if rec.stage_id.state == 'approve':
#                request_date = datetime.strptime(rec.request_date,"%Y-%m-%d")
#                current_date = datetime.strptime(fields.Date.today(),"%Y-%m-%d")
#                rec.days_not_acted = (current_date - request_date).days
#                print ("________-----------------rec.days_not_acted",rec.days_not_acted)
#                rec.is_approve = True

    @api.depends('custom_frequency_start_date', 'custom_maintenance_frequence')
    def _compute_next_date(self):
        for rec in self:
            if rec.custom_maintenance_frequence == 'daily':
                if rec.custom_frequency_start_date:
                    start_date = datetime.strptime(rec.custom_frequency_start_date, "%Y-%m-%d")
                    rec.custom_frequency_next_date =  start_date + relativedelta(days=+1)
            elif rec.custom_maintenance_frequence == 'weekly':
                if rec.custom_frequency_start_date:
                    start_date = datetime.strptime(rec.custom_frequency_start_date, "%Y-%m-%d")
                    rec.custom_frequency_next_date =  start_date + relativedelta(days=+7)
            elif rec.custom_maintenance_frequence == 'monthly':
                if rec.custom_frequency_start_date:
                    start_date = datetime.strptime(rec.custom_frequency_start_date, "%Y-%m-%d")
                    rec.custom_frequency_next_date =  start_date + relativedelta(months=+1)
            elif rec.custom_maintenance_frequence == 'quarterly':
                if rec.custom_frequency_start_date:
                    start_date = datetime.strptime(rec.custom_frequency_start_date, "%Y-%m-%d")
                    rec.custom_frequency_next_date =  start_date + relativedelta(months=+3)
            elif rec.custom_maintenance_frequence == 'semiannual':
                if rec.custom_frequency_start_date:
                    start_date = datetime.strptime(rec.custom_frequency_start_date, "%Y-%m-%d")
                    rec.custom_frequency_next_date =  start_date + relativedelta(months=+6)
            elif rec.custom_maintenance_frequence == 'annual':
                if rec.custom_frequency_start_date:
                    start_date = datetime.strptime(rec.custom_frequency_start_date, "%Y-%m-%d")
                    rec.custom_frequency_next_date =  start_date + relativedelta(years=+1)
    @api.depends('close_date')
    def _compute_days_overdue(self):
        for rec in self:
            if rec.close_date and rec.custom_estimate_completion_date:
                d1 = rec.close_date
                d2 = rec.custom_estimate_completion_date
                delta = d1 - d2
                rec.custom_days_overdue = delta.days#datetime.strptime(str(rec.close_date, "%Y-%m-%d")) - datetime.strptime(str(rec.custom_estimate_completion_date, "%Y-%m-%d")).days

    @api.depends('custom_line_ids')
    def _compute_total_cost(self):
        for rec in self:
            for line in rec.custom_line_ids:
                rec.custom_total_cost += line.sub_total

    @api.depends('custom_line_ids')
    def _compute_lines(self):
        for rec in self:
            rec.custom_number_of_lines = len(rec.custom_line_ids)

    @api.depends('custom_line_ids')
    def _compute_number_of_qty(self):
        for rec in self:
            rec.custom_number_of_qty = sum(line.quantity for line in rec.custom_line_ids)

    state = fields.Selection(
        string='State',
        related='stage_id.state',
        store=True,
    )
    custom_number = fields.Char(
        string='Number',
        readonly=True,
    )
    custom_asset_id = fields.Many2one(
        'account.asset.asset.custom',
        string="Asset",
    )
    custom_user_id = fields.Many2one(
        'res.users',
        string='Responsible User',
        default=lambda self: self.env.user.id, 
    )
    custom_department_id = fields.Many2one(
        'hr.department',
        string="Department",
    )
    custom_subject = fields.Char(
        string='Subject',
    )
    custom_detail = fields.Char(
        string='Description Detail',
    )
    custom_is_contract = fields.Boolean(
        string='Is Maintenance Contract',
    )
    custom_line_ids = fields.One2many(
        'custom.maintenance.line',
        'maintenance_id',
        string='Maintenance Line',
    )
    custom_maintenance_frequence = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semiannual', 'Semi-Annual'),
        ('annual', 'Annual')],
        default='daily',
    )
    custom_frequency_start_date = fields.Date(
        string='Frequency Start Date',
    )
    custom_frequency_next_date = fields.Date(
        string='Frequency Next Date',
        compute='_compute_next_date',
        store=True,
    )
    custom_days_not_acted = fields.Float(
        string='Days Not Acted',
#        compute='_days_not_acted',
#        store=True,
    )
    custom_estimate_completion_days = fields.Integer(
        string='Estimate Completion Days',
    )
    custom_estimate_completion_date = fields.Date(
        string='Estimate Completion Date',
        readonly=True,
#        compute='_estimate_completion_date',
#        store=True,
    )
    custom_employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1),
    )
    custom_is_approve = fields.Boolean(
        string='Is Approve',
    )
    custom_maintenance_completion_date = fields.Date(
        string='Maintenance Completed Date',
        readonly=True,
    )
    custom_diagnosis_id = fields.Many2one(
        'maintenance.diagnosis',
        string='Maintenance Diagnosis',
    )
    custom_activity_id = fields.Many2one(
        'maintenance.activity',
        string='Maintenance Activity',
    )
    custom_previous_maintenance_id = fields.Many2one(
        'maintenance.request',
        string='Previous Maintenance',
        readonly=True,
    )
    custom_maintenance_analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string="Analytic Account",
    )
    custom_days_overdue = fields.Integer(
        string="Days Overdue",
        compute="_compute_days_overdue",
        store=True,
    )
    custom_total_cost = fields.Float(
        string="Total Cost",
        compute="_compute_total_cost",
        store=True
    )
    custom_number_of_lines = fields.Float(
        string="Number of Lines",
        compute="_compute_lines",
        store=True,
    )
    custom_number_of_qty = fields.Float(
        string="Number of Quantity",
        compute="_compute_number_of_qty",
        store=True
    )

    @api.model
    def create(self, vals):
        number = self.env['ir.sequence'].next_by_code('maintenance.request.seq')
        vals.update({
        'custom_number': number
        })
        res = super(MaintenanceRequest, self).create(vals)
        return res
    
    def _state_approve(self):
        request_date = self.request_date
        current_date = fields.Date.today()
        self.custom_days_not_acted = (current_date - request_date).days
        self.custom_is_approve = True
        return True
    
    @api.multi
    def write(self, vals):
        for rec in self:
            if vals.get('stage_id'):
                stage = self.env['maintenance.stage'].browse(int(vals.get('stage_id')))
                if stage and stage.state == 'approve':
                    rec._state_approve()
                if stage and stage.state == 'submit':
                    rec.custom_estimate_completion_date = (datetime.today() + relativedelta(days=rec.custom_estimate_completion_days)).date()
        return super(MaintenanceRequest, self).write(vals)

#     @api.multi
#     def create_order(self):
#         for rec in self:
#             lines = []
#             for line in rec.custom_line_ids:
#                 original_qty = line.quantity - line.old_qty
#                 if original_qty > 0:
#                     line.old_qty += line.quantity
#                     line_vals = {
#                     'requisition_type': line.line_type,
#                     'product_id': line.product_id.id,
#                     'description': line.custom_description,
#                     'qty': original_qty,
#                     'uom': line.uom_id.id,
# #                    'requisition_id': purchase_requisition.id,
#                     }
#                     lines.append((0,0,line_vals))
#             if lines:
#                 requisition_vals = {
#                     'employee_id': rec.custom_employee_id.id,
#                     'requisiton_responsible_id': rec.custom_employee_id.id,
#                     'company_id': self.env.user.company_id.id,
#                     'request_date': rec.request_date,
#                     'maintenance_id': rec.id,
#                     'requisition_line_ids' : lines,
#                 }
#                 if rec.maintenance_type == 'preventive':
#                     requisition_vals.update({
#                         'department_id': rec.custom_department_id.id,
#                     })
#                 purchase_requisition_id = self.env['material.purchase.requisition'].create(requisition_vals)
#                 action = self.env.ref('material_purchase_requisitions.action_material_purchase_requisition').read()[0]
#                 action['domain'] = [('id', 'in', purchase_requisition_id.ids)]
#                 return action
#                self.env['material.purchase.requisition.line'].create(line_vals)

    # @api.multi
    # def show_requisition(self):
    #     self.ensure_one()
    #     res = self.env.ref('material_purchase_requisitions.action_material_purchase_requisition')
    #     res = res.read()[0]
    #     res['domain'] = str([('maintenance_id', '=', self.id)])
    #     return res

    @api.multi
    def submit_to_manager(self):
        for rec in self:
            stage = self.env['maintenance.stage'].search([('state', '=', 'submit')], limit=1)
            if stage:
                custom_estimate_completion_date = datetime.today() + relativedelta(days=rec.custom_estimate_completion_days)
                rec.write({
                    'stage_id': stage.id,
                    'custom_estimate_completion_date': (datetime.today() + relativedelta(days=rec.custom_estimate_completion_days)).date()
                })
    #            rec.state = 'submit'
#                 rec.estimate_completion_date = datetime.today() + relativedelta(days=+rec.estimate_completion_days)

    @api.multi
    def approve_maintenance(self):
        for rec in self:
            stage = self.env['maintenance.stage'].search([('state', '=', 'approve')], limit=1)
            if stage:
                rec.write({'stage_id': stage.id})
#            rec.state = 'approve'

    @api.multi
    def receive_request(self):
        for rec in self:
            stage = self.env['maintenance.stage'].search([('state', '=', 'todo')], limit=1)
            if stage:
                rec.write({'stage_id': stage.id})
#            rec.state = 'todo'

    @api.multi
    def start_maintenance(self):
        for rec in self:
            stage = self.env['maintenance.stage'].search([('state', '=', 'inprogress')], limit=1)
            if stage:
                rec.write({'stage_id': stage.id})
#            rec.state = 'inprogress'

    @api.multi
    def maintenance_complete(self):
        for rec in self:
            stage = self.env['maintenance.stage'].search([('state', '=', 'done')], limit=1)
            if stage:
                rec.write({
                    'stage_id': stage.id,
                    'custom_maintenance_completion_date': fields.Date.today(),
                })
#                 rec.maintenance_completion_date = fields.Date.today()
#            rec.state = 'done'

    @api.multi
    def reset_to_draft(self):
        for rec in self:
            stage = self.env['maintenance.stage'].search([('state', '=', 'draft')])
            rec.write({
                'stage_id': stage.id,
#                 'state': 'draft'
            })
#             rec.state = 'draft'
    
    @api.multi
    def _cancel_maintenance(self):
        stage = self.env['maintenance.stage'].search([('state', '=', 'cancel')], limit=1)
        for rec in self:
            if stage:
                rec.write({'stage_id': stage.id})

    @api.multi
    def archive_equipment_request(self):
        res = super(MaintenanceRequest, self).archive_equipment_request()
        self._cancel_maintenance()
        return res

    @api.multi
    def act_cancel_maintenance(self):
        self._cancel_maintenance()
        self.write({'archive': True})
    
    @api.multi
    def act_cancel_maintenance_manager(self):
        self._cancel_maintenance()
        self.write({'archive': True})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
