from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    def _get_default_auto_lock_time(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'th_pos_lock_screen.auto_lock_time')

    auto_lock_time = fields.Integer(string='Auto Lock Time',
                                    default=_get_default_auto_lock_time)
