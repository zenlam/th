from odoo import api, fields, models, _


class THTimeRange(models.Model):
    _name = 'th.time.range'
    _description = 'TH Time Range'
    _order = 'sequence'

    sequence = fields.Integer(help='Gives the sequence order when displaying '
                                   'a list of Time Range.')
    name = fields.Char('Name', required=True)
    start_time = fields.Float('Starting Hours', required=True,
                              help='24hrs Format')
    end_time = fields.Float('Ending Hours', required=True,
                            help='24hrs Format')

    _sql_constraints = [('th_time_range_name_unique', 'unique(name)',
                         'Name is already exists.')]
