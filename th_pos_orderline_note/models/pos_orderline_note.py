from odoo import api, fields, models, _


class ThOrderlineNote(models.Model):
    _name = 'th.orderline.note'
    _description = 'TH Orderline Note'
    _order = 'sequence'

    sequence = fields.Integer(help="Gives the sequence order when displaying "
                                   "a list of notes.")
    name = fields.Char('Name', required=True)
