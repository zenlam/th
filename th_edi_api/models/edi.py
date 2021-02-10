# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.tools import config
import pysftp
import logging
import os

_logger = logging.getLogger(__name__)
#
# sftp_host = config.get_misc('edi-integration', 'sftp_host')
# sftp_port = int(config.get_misc('edi-integration', 'sftp_port'))
# sftp_user = config.get_misc('edi-integration', 'sftp_user')
# sftp_password = config.get_misc('edi-integration', 'sftp_password')

# edi_input_path = config.get_misc('edi-integration', 'edi_input_path')
# edi_output_path = config.get_misc('edi-integration', 'edi_output_path')
odoo_input_path = config.get_misc('edi-integration', 'odoo_input_path')
odoo_output_path = config.get_misc('edi-integration', 'odoo_output_path')


class EDIAPI(models.AbstractModel):
    """
    Abstract model for any model use to communicate with EDI System
    TODO: After we have EDI System info, we will build api function to send and receive csv data
    """
    _name = 'th.edi.api'
    _description = 'Abstract Model to Communicate with EDI System'
    _declare = {

    }

    def _sftp_put(self, local_file, remote_path):
        """

        :param local_file: string
        :param remote_path: string
        :return: boolean
        """
        if self.env.context.get('company_id'):
            company = self.env['res.company'].browse(self.env.context.get('company_id'))
        else:
            company = self.env.user.company_id
        sftp_host = company.edi_server
        sftp_user = company.edi_username
        sftp_password = company.edi_password
        sftp_port = company.edi_port
        edi_input_path = company.edi_input

        _edi_input_path = edi_input_path
        if remote_path is not None:
            _edi_input_path = os.path.join(edi_input_path, remote_path)

        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        with pysftp.Connection(host=sftp_host, username=sftp_user, password=sftp_password, port=sftp_port, cnopts=cnopts) as sftp:
            sftp.put(local_file, os.path.join(_edi_input_path, os.path.basename(local_file)))
        return True

    def _sftp_get(self, remote_file, local_path):
        """

        :param remote_file: string
        :param local_path: string
        :return: boolean
        """
        if self.env.context.get('company_id'):
            company = self.env['res.company'].browse(self.env.context.get('company_id'))
        else:
            company = self.env.user.company_id
        sftp_host = company.edi_server
        sftp_user = company.edi_username
        sftp_password = company.edi_password
        sftp_port = company.edi_port

        edi_output_path = company.edi_output
        _edi_output_path = edi_output_path
        if remote_file is not None:
            _edi_output_path = os.path.join(edi_output_path, remote_file)

        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        with pysftp.Connection(host=sftp_host, username=sftp_user, password=sftp_password, port=sftp_port, cnopts=cnopts) as sftp:
            sftp.get(_edi_output_path, local_path)
        return True

    def _sftp_delete(self, remote_file):
        """

        :param remote_file: string
        :return: boolean
        """
        if self.env.context.get('company_id'):
            company = self.env['res.company'].browse(self.env.context.get('company_id'))
        else:
            company = self.env.user.company_id
        sftp_host = company.edi_server
        sftp_user = company.edi_username
        sftp_password = company.edi_password
        sftp_port = company.edi_port
        edi_input_path = company.edi_input

        with pysftp.Connection(host=sftp_host, username=sftp_user, password=sftp_password, port=sftp_port) as sftp:
            sftp.remove(remote_file)
        return True

    @api.model
    def send_csv(self, csv_data=None, csv_path=None, dest_path=None, *args, **kwargs):
        """
        Use to send csv to EDI System
        Ex: self.env['th.edi.api'].send_csv(csv_path='/tmp/havi.8uf7FHi.tmp.csv')
        :param csv_data: 2D array - Ex: [['abc', 'def', ...], ...]
        :param csv_path: string - absolute path in storage
        :param dest_path: string - path in sftp server
        :param args: additional parameters
        :param kwargs: additional parameters
        :return:
        """
        _logger.info('[EDI API] Start to transfer {csv} to {dest}'.format(csv=csv_path, dest=dest_path))
        try:
            _logger.info('[EDI API] Transferring {csv} to {dest}'.format(csv=csv_path, dest=dest_path))
            self._sftp_put(csv_path, dest_path)
            self.env['th.edi.log'].create_log(
                name=os.path.basename(csv_path),
                type='put'
            )
        except Exception as e:
            self.env['th.edi.log'].create_log(
                name=csv_path,
                type='put',
                note=e.__repr__(),
                state='fail'
            )

    @api.multi
    def receive_csv(self, csv_data, filename=None, model=None, func_name=None, *args, **kwargs):
        """
        This function will be triggered once server receive csv from EDI.

        If EDI system cannot pass parameter for model and function name,
        we need to convention the filename to trigger corresponding model function

        :param csv_data: csv data format
        :param filename: string - file name
        :param model: model name that use to call function
        :param func_name: function name of model that use to process csv data
        :param args:
        :param kwargs:
        :return:
        """
        def crush(f):
            """
            TODO: to do later
            :param f: filename or full file path
            :return:
            """

            return '_', '_'

        if not (model and func_name):
            model, func_name = crush(filename)
        return getattr(self.env[model], func_name)(csv_data)

