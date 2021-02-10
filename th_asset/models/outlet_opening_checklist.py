# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class OutletOpeningChecklist(models.Model):
    _name = 'outlet.opening.checklist'

    name = fields.Char(string='Checklist Name',
                       required=True,
                       copy=False)
    create_uid = fields.Many2one('res.users',
                                 string='Created By',
                                 default=lambda self: self.env.user)
    checklist_line_ids = fields.One2many('opening.checklist.line',
                                         inverse_name='checklist_id',
                                         string='Product Line',
                                         required=True)


class OpeningChecklistLine(models.Model):
    _name = 'opening.checklist.line'

    checklist_id = fields.Many2one('outlet.opening.checklist',
                                   string='Opening Checklist Id',
                                   readony=True)
    asset_id = fields.Many2one('account.asset.asset.custom',
                               string='Products',
                               required=True)
