# -*- coding: utf-8 -*-

from odoo import models, fields


class MaintenanceStage(models.Model):
    _inherit = 'maintenance.stage'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('todo', 'To Do'),
        ('inprogress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),],
        default='draft',
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
