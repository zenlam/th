# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    asset_prepayment_account = fields.Many2one('account.account')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    asset_prepayment_account = fields.Many2one(
        'account.account', string="Asset Prepayment Account",
        related='company_id.asset_prepayment_account',
        domain=lambda self: [('company_id', '=', self.env.user.company_id.id)],
        readonly=False
        )
