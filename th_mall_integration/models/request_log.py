from odoo import fields, models, api, _


class ThApiLog(models.Model):
    _name = 'th.request.log'
    _description = 'TH Mall Integration Request Log'
    _order = 'name DESC'

    config_id = fields.Many2one('th.request.config', string="Config")
    name = fields.Datetime(string="Date")
    log_detail_ids = fields.One2many(
        'th.request.log.details',
        inverse_name='log_id'
    )

    def log(self, info):
        """
        Save log details
        @param info: dict - log information
        @return:
        """
        self.ensure_one()
        self.write({'log_detail_ids': info})


class ThApiLogDetails(models.Model):
    _name = 'th.request.log.details'
    _description = 'TH Mall Integration Request Log Details'

    details = fields.Text(string="Response")
    data = fields.Text(string="Sent Data")
    status = fields.Selection([('failed', 'Failed'), ('success', 'Success')],
                              string="Status")
    request_id = fields.Many2one('th.request.details', string="Details")
    log_id = fields.Many2one('th.request.log')
