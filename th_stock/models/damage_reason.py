from odoo import models, fields, api, _


class DamageReason(models.Model):
    _name = 'damage.reason'
    _description = 'TH Damage Reason'

    name = fields.Char(string="Description")
    active = fields.Boolean(string="Active", default=True)
