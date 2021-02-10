from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    output_tax_conf = fields.Boolean("Output Tax Configuration")
