# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class EDITransferLog(models.Model):
    _name = 'th.edi.log'

    name = fields.Char(string=_('Log Name'))
    type = fields.Selection(selection=[('put', _('Send')),
                                       ('get', _('Receive'))],
                            string=_('Transfer Type'))
    ref = fields.Char(string=_('Ref'))
    note = fields.Text(string=_('Note'))
    time = fields.Datetime(string=_('Start Time'))
    state = fields.Selection(selection=[('done', _('Done')),
                                        ('fail', _('Fail'))],
                             string=_('Status'), )

    @api.model
    def create_log(self, name, type, state='done', note=None):
        """

        :param name:
        :param type:
        :param status:
        :param note:
        :return:
        """
        return self.create([{
            'name': name,
            'type': type,
            'state': state,
            'note': note,
            'time': fields.Datetime.now(),
            'ref': self.env.context.get('ref')
        }])
