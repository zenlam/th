# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, SUPERUSER_ID

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    removal_date = fields.Date(related='lot_id.removal_date', string='Expiry Date')