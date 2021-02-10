# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class AssetFormCapitalisedWizard(models.TransientModel):
    _name = 'asset.form.capitalised.wizard'

    @api.model
    def _get_code(self):
        active_id = self.env.context.get('active_id', False)
        if active_id:
            return self.env['account.asset.asset.custom'].browse(active_id).code
        return ''

    code = fields.Char('Reference', default=_get_code)

    def update_capitalized_checkbox(self):
        active_id = self.env.context.get('active_id', False)

        asset = self.env['account.asset.asset.custom'].browse(active_id)

        if asset:
            asset.write({'capitalised_later': False})
        return {'type': 'ir.actions.act_window_close'}
