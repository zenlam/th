# -*- coding: utf-8 -*-

from odoo import models, fields


class MaintenanceTeam(models.Model):
    _inherit = 'maintenance.team'

    number = fields.Char(
        string='Number',
        readonly=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string="Partner",
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
    )
    department_id = fields.Many2one(
        'hr.department',
        string="Department",
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
