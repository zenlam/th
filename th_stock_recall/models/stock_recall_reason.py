# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class RecallReason(models.Model):
    _name = 'stock.recall.reason'

    name = fields.Char(string=_('Reason Name'))
    description = fields.Text(string=_('Description'))
