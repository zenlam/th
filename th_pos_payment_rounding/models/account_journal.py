# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from openerp.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_rounding_method = fields.Boolean(string='Rounding Payment Method',
                                        default=False,
                                        help='Tick this if this payment '
                                             'method is a rounding payment '
                                             'method.\nNote: Company can only '
                                             'have one rounding payment '
                                             'method.')

    @api.constrains('company_id', 'is_rounding_method')
    def _check_is_rounding_method(self):
        """ Ensure there will be only one rounding payment method per company
        """
        count = len(self.search([('company_id', '=', self.company_id.id),
                                 ('is_rounding_method', '=', True)]))
        if count > 1:
            raise ValidationError(_('There can be only one rounding payment '
                                    'method per company.'))
