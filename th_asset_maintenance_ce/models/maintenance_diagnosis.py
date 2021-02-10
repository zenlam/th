# -*- coding: utf-8 -*-

from odoo import models, fields


class MaintenanceDiagnosis(models.Model):
    _name = 'maintenance.diagnosis'

    name = fields.Char(
        string='Name',
        required=True,
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
