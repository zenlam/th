# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CashControl(models.Model):
    """
    This model is used in Put Money In and Take Money Out in the POS session
    and make accounting posting.
    """
    _name = 'cash.control'

    def _default_company_id(self):
        """
        Get the company of the user
        """
        return self.env.user.company_id

    @api.multi
    def toggle_active(self):
        """
        Inverse the value of field 'active' on the records in 'self'.
        """
        for record in self:
            record.active = not record.active

    name = fields.Char(string='Name', help='Reason Name', required=1)
    action = fields.Selection(selection=[('put_in', 'Put In'),
                                         ('failed_bank_in', 'Failed Bank In'),
                                         ('take_out', 'Take Out'),
                                         ('bank_in', 'Bank In')],
                              string='Action',
                              required=1)
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 required=1,
                                 default=_default_company_id)
    debit_account_id = fields.Many2one('account.account',
                                       string='Debit Account',
                                       required=1)
    credit_account_id = fields.Many2one('account.account',
                                        string='Credit Account',
                                        required=1)
    active = fields.Boolean(string='Active',
                            default=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name, company_id)',
         'The cash control name must be unique !'),
    ]
