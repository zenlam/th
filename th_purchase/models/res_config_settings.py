# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    po_order_approval = fields.Boolean(string="1st Level Purchase Order Approval",
                                       default=lambda self: self.env.user.company_id.po_double_validation in ['two_step','three_step'])
    po_double_validation = fields.Selection(related='company_id.po_double_validation', string="Levels of Approvals *",
                                            readonly=False)
    # in UI string is 2nd but internally odoo consider third level approval for PO [JUST LABEL IS 2nd DONT Confuse ((^_^) ]
    po_third_order_approval = fields.Boolean(string="2nd Level Purchase Order Approval",
                                       default=lambda self: self.env.user.company_id.po_double_validation == 'three_step')
    po_tripple_validation_amount = fields.Monetary(related='company_id.po_tripple_validation_amount',
                                                  string="Minimum Amount", currency_field='company_currency_id',
                                                  readonly=False)

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        po_validation = 'one_step'
        po_double_validation_amount = 0.0
        po_tripple_validation_amount = 0.0
        if self.po_order_approval and self.po_third_order_approval:
            po_validation = 'three_step'
            po_double_validation_amount = self.po_double_validation_amount
            po_tripple_validation_amount = self.po_tripple_validation_amount
            if self.po_tripple_validation_amount < self.po_double_validation_amount:
                raise ValidationError(
                    "Minimum amount of the second approval should be greater then the minimum amount of the first approval !")
        elif self.po_order_approval and not self.po_third_order_approval:
            po_validation = 'two_step'
            po_double_validation_amount = self.po_double_validation_amount

        self.po_double_validation_amount = po_double_validation_amount
        self.po_tripple_validation_amount = po_tripple_validation_amount
        self.po_double_validation = po_validation

