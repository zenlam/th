# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    analytic_account_id = fields.Many2one(required=1)

    @api.multi
    def _prepare_invoice(self):
        """ Prepare the dict of values to create the new invoice for a sales order.
        Note: This function return the invoice values dict to the previous function to create an invoice when the user
        creates invoice from SO.
        """
        res = super(SaleOrder, self)._prepare_invoice()
        res.update({
            'account_analytic_id': self.analytic_account_id.id,
        })
        return res