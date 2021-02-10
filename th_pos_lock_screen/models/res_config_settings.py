from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_lock_time = fields.Integer(
        string='Auto Lock Time',
        config_parameter='th_pos_lock_screen.auto_lock_time')
