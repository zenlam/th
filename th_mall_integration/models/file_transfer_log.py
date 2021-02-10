from odoo import models, fields, api, _
import base64


class ThFileTransferLog(models.Model):
    _name = 'th.file.transfer.log'
    _description = 'TH Mall Integration FTP Log'
    _order = 'id desc'

    file_name = fields.Char(string="Filename")
    date_transfer = fields.Datetime(string="Date Transfer")
    state = fields.Selection([('done', 'Done'), ('except', 'Except')],
                             string="State")
    note = fields.Text(string='Note')
    company_id = fields.Many2one('res.company', string="Company")
    outlet_id = fields.Many2one('stock.warehouse', string="Outlet")
    file = fields.Binary(string="File to Download", readonly=True)
    result = fields.Char(compute='get_result')

    @api.multi
    def get_result(self):
        for log in self:
            if log.file:
                log.result = base64.decodebytes(log.file)
