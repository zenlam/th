from odoo import fields, models, api, _
import pysftp
from ftplib import FTP
from odoo.exceptions import UserError


class ThFileTransferConfig(models.Model):
    _name = 'th.file.transfer.config'
    _description = 'TH Mall Integration FTP Configuration'

    name = fields.Char(string="Name")
    active = fields.Boolean(string="Active", default=True)
    prefix = fields.Char(string="Prefix")
    machine = fields.Char(string="Machine ID")
    date_format = fields.Char(string="Date Format", default='%Y%m%d')
    filename_date_format = fields.Char(string="File Name Date Format",
                                       default='%Y%m%d')
    padding = fields.Integer(string="Padding Sale Number")
    ip = fields.Char(string="FTP Server")
    port = fields.Integer(string="Port", default=21)
    gst_padding = fields.Integer(string="Padding GST Number")
    cash_padding = fields.Integer(string="Padding Cash Payment")
    other_padding = fields.Integer(string="Padding Other Payment")
    discount_padding = fields.Integer(string="Padding Discount Number")
    ticket_count_padding = fields.Integer(string="Padding Ticket Count Number")
    password = fields.Char(string="Password")
    outlet_id = fields.Many2one('stock.warehouse', string="Outlet")
    before_gst_padding = fields.Integer(string="Padding Before GST Number")
    position = fields.Char(string="Data Format")
    name_file = fields.Char(string="File Name")
    period = fields.Selection([('daily', 'Daily'), ('monthly', 'Monthly')],
                              default='daily', string="Period")
    type = fields.Selection([('ftp', 'FTP'), ('sftp', 'SFTP')],
                            default='ftp',
                            string="Type")
    data_type = fields.Selection([('summary', 'Summary'),
                                  ('detail', 'Detail')], default='summary')
    sequence = fields.Integer(string="Sequence", default=000)
    next_number = fields.Integer(string="Next Number", default=1)
    last_modified_seq = fields.Date(string="Last modified seq")
    sequence_padding = fields.Integer(string="Padding Sequence", default=1)
    is_passive_mode = fields.Boolean(string="Passive Mode", default=True)
    company_id = fields.Many2one('res.company', string="Company",
                                 required=True,
                                 default=lambda self: self.env.user.company_id)
    is_client_request = fields.Boolean(string="Client Request",
                                       default=False,
                                       help='If this is true, system will not '
                                            'transfer the GTO report to the '
                                            'FTP server since the client will '
                                            'request the report.')
    transfer_directory = fields.Char(string="FTP / SFTP Directory",
                                     help='Leave this empty if you want to '
                                          'store the file in the first '
                                          'directory after login.\n'
                                          'Example: Sent')

    @api.multi
    def test_connection(self):
        """
        Test connection to server
        @return:
        """
        if self.type == 'ftp':
            self.ftp_connect()
        elif self.type == 'sftp':
            self.sftp_connect()
        raise UserError(_("Success !"))

    def ftp_connect(self):
        try:
            ftp = FTP(self.ip)
            if not self.is_passive_mode:
                ftp.set_pasv(False)
            ftp.connect(self.ip, int(self.port))
            ftp.login(self.machine, self.password)
            ftp.close()
        except Exception as e:
            raise UserError(str(e))

    def sftp_connect(self):
        try:
            ip = self.ip
            username = self.machine
            password = self.password or ''
            port = int(self.port)
            with pysftp.Connection(ip, username=username, password=password,
                                   port=port) as connection:
                connection.listdir()
        except Exception as e:
            raise UserError(str(e))
