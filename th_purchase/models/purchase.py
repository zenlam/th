# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # Note : again label is 2nd but technically its third approval as considering odoo base
    state = fields.Selection(
        selection_add=[('to approve', 'To 1st Approval'),('to_third_approve', 'To 2nd Approval')])


    # NOTE: overwrite whole button confirm method as approval worflow needs to change.
    # TODO : Change dependency of purchase module after merging the Purchase requisition task, as same method inherited in requisition module
    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double/Tripple validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or  (
                            (
                                order.company_id.po_double_validation == 'two_step'
                                and order.amount_total < self.env.user.company_id.currency_id._convert(
                                order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
                                order.date_order or fields.Date.today())
                            )
                            or order.user_has_groups('purchase.group_purchase_manager')
                        )\
                    or (
                            (
                                order.company_id.po_double_validation == 'three_step' \
                                and order.amount_total < self.env.user.company_id.currency_id._convert(
                                order.company_id.po_tripple_validation_amount, order.currency_id, order.company_id,
                                order.date_order or fields.Date.today())
                            )
                            or order.user_has_groups('th_purchase.group_purchase_second_approval_manager')
                        ):
                order.button_approve()

            elif order.company_id.po_double_validation == 'two_step' \
                and order.amount_total > self.env.user.company_id.currency_id._convert(
                    order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
                    order.date_order or fields.Date.today()) \
                and not order.user_has_groups('purchase.group_purchase_manager'):
                order.write({'state': 'to approve'})

            elif order.company_id.po_double_validation == 'three_step' \
                and order.amount_total > self.env.user.company_id.currency_id._convert(
                    order.company_id.po_tripple_validation_amount, order.currency_id, order.company_id,
                    order.date_order or fields.Date.today()):

                if not order.user_has_groups('purchase.group_purchase_manager'):
                    order.write({'state': 'to approve'})
                if order.user_has_groups('purchase.group_purchase_manager') and not order.user_has_groups('th_purchase.group_purchase_second_approval_manager'):
                    order.write({'state': 'to_third_approve'})
        return True

    @api.multi
    def button_approve(self, force=False):
        for order in self:
            if order.state == 'to approve':
                # Deal with Tripple validation process
                if (order.company_id.po_double_validation == 'three_step' \
                            and order.amount_total < self.env.user.company_id.currency_id._convert(
                            order.company_id.po_tripple_validation_amount, order.currency_id, order.company_id,
                            order.date_order or fields.Date.today())) \
                        or order.user_has_groups('th_purchase.group_purchase_second_approval_manager'):
                    super(PurchaseOrder, order).button_approve(force=force)
                else:
                    order.write({'state': 'to_third_approve'})
            else:
                super(PurchaseOrder, order).button_approve(force=force)
        return {}

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    account_analytic_id = fields.Many2one(required=1)

    @api.multi
    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line.
        Note: This function returns a list of dictionary ready to be used in stock.move's create()
        """
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        for r in res:
            r.update({
                'account_analytic_id': self.account_analytic_id.id,
            })
        return res
