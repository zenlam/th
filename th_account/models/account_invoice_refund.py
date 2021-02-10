# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountInvoiceRefund(models.TransientModel):
    _inherit = 'account.invoice.refund'

    def _get_filter_refund_selection(self):
        context = self.env.context or {}
        if context.get('from_vendor_bill') and context.get('from_vendor_bill') is True:
            return [('refund', 'Create a draft debit note'), ('cancel', 'Cancel: create debit note and reconcile'),
                    ('modify', 'Modify: create debit note, reconcile and create a new draft invoice')]
        return [('refund', 'Create a draft credit note'), ('cancel', 'Cancel: create credit note and reconcile'),
                ('modify', 'Modify: create credit note, reconcile and create a new draft invoice')]

    filter_refund = fields.Selection(selection=_get_filter_refund_selection)
