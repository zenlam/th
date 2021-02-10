from odoo import models, fields, api, _
from ..models.api_caller import ApiCaller


class ThRunRequestConfig(models.TransientModel):
    _name = 'th.run.request.config'
    _description = 'TH Mall Integration Run Request Configuration'

    date = fields.Date(string="Date", required=1)
    config_id = fields.Many2one('th.request.config')

    @api.model
    def default_get(self, fields):
        res = {}
        active_id = self._context.get('active_id')
        if active_id:
            res = {'config_id': active_id}
        return res

    @api.one
    def run(self):
        ApiCaller(self.config_id).run(self.date)
