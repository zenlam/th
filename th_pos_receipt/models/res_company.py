# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = "res.company"

    # Here add new field at company level to change footer at one place for all outlet (pos.config)
    pos_footer_mesage = fields.Char("POS Footer")