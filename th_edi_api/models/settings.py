# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import models, api, fields, _


class Settings(models.TransientModel):
    _inherit = 'res.config.settings'

    edi_server = fields.Char(string=_('IDE Server IP'), related='company_id.edi_server', readonly=False, required=True)
    protocol = fields.Selection(selection=[('sftp', 'SFTP'),
                                           ('ftp', 'FTP'),
                                           ('scp', 'SCP')], related='company_id.protocol', readonly=False,
                                default='sftp', string=_('Transfer Protocol'), required=True)
    edi_username = fields.Char(string=_('Username'), related='company_id.edi_username',
                               readonly=False, default='sftp-user', required=True)
    edi_password = fields.Char(string=_('Password'), related='company_id.edi_password', readonly=False, required=True)
    edi_port = fields.Integer(string=_('Port'), related='company_id.edi_port', readonly=False, required=True)
    edi_input = fields.Char(string=_('Input Folder'), help=_('The folder using for Odoo push csv file to HAVI'),
                            related='company_id.edi_input', readonly=False, required=True)
    edi_output = fields.Char(string=_('Output Folder'), help=_('The folder using for Odoo pull csv file from HAVI'),
                             related='company_id.edi_output', readonly=False, required=True)


class ResCompany(models.Model):
    _inherit = 'res.company'

    edi_server = fields.Char(string=_('IDE Server IP'))
    protocol = fields.Selection(selection=[('sftp', 'SFTP'),
                                           ('ftp', 'FTP'),
                                           ('scp', 'SCP')],
                                default='sftp', string=_('Transfer Protocol'))
    edi_username = fields.Char(string=_('Username'))
    edi_password = fields.Char(string=_('Password'))
    edi_port = fields.Integer(string=_('Port'))
    edi_input = fields.Char(string=_('Input Folder'), help=_('The folder using for Odoo push csv file to HAVI'))
    edi_output = fields.Char(string=_('Output Folder'), help=_('The folder using for Odoo pull csv file from HAVI'))
