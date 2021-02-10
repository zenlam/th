from odoo import models, fields, api, _
from werkzeug import url_encode


class ThExpenseSheetRegisterPaymentWizard(models.TransientModel):
    _inherit = 'hr.expense.sheet.register.payment.wizard'

    analytic_account_id = fields.Many2one('account.analytic.account',
                                          string='Analytic Account',
                                          required=1)

    @api.model
    def _default_partner_id(self):
        """
        NOTE: override method because this wizard is not anymore open from
              expense report, instead it is open from expense
        """
        context = dict(self._context or {})
        # changes the way to get the expense_sheet
        active_ids = context.get('active_ids', [])
        expense_id = self.env['hr.expense'].browse(active_ids)
        expense_sheet = self.env['hr.expense.sheet'].search([
            ('id', '=', expense_id.sheet_id.id)
        ])
        return expense_sheet.address_id.id or \
               expense_sheet.employee_id.id and \
               expense_sheet.employee_id.address_home_id.id

    partner_id = fields.Many2one('res.partner', string='Partner',
                                 required=True, default=_default_partner_id)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """
        NOTE: override method because this wizard is not anymore open from
              expense report, instead it is open from expense
        """
        active_ids = self._context.get('active_ids', [])
        expense_id = self.env['hr.expense'].browse(active_ids)
        expense_sheet = self.env['hr.expense.sheet'].search([
            ('id', '=', expense_id.sheet_id.id)
        ])
        if expense_sheet.employee_id.id and \
                expense_sheet.employee_id.sudo().bank_account_id.id:
            self.partner_bank_account_id = \
                expense_sheet.employee_id.sudo().bank_account_id.id
        elif self.partner_id and len(self.partner_id.bank_ids) > 0:
            self.partner_bank_account_id = self.partner_id.bank_ids[0]
        else:
            self.partner_bank_account_id = False

    @api.multi
    def expense_post_payment(self):
        """
        NOTE: override method because this wizard is not anymore open from
              expense report, instead it is open from expense
        """
        self.ensure_one()
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        expense_id = self.env['hr.expense'].browse(active_ids)
        expense_sheet = self.env['hr.expense.sheet'].search([
            ('id', '=', expense_id.sheet_id.id)
        ])
        # Create payment and post it
        payment = self.env['account.payment'].create(self._get_payment_vals())
        payment.post()

        # Log the payment in the chatter
        body = (_(
            "A payment of %s %s with the reference <a href='/mail/view?%s'>%s</a> related to your expense %s has been made.") % (
                payment.amount, payment.currency_id.symbol,
                url_encode({'model': 'account.payment', 'res_id': payment.id}),
                payment.name, expense_sheet.name))
        expense_sheet.message_post(body=body)

        # Reconcile the payment and the expense, i.e. lookup on the payable account move lines
        account_move_lines_to_reconcile = self.env['account.move.line']
        for line in payment.move_line_ids + expense_sheet.account_move_id.line_ids:
            if line.account_id.internal_type == 'payable' and not line.reconciled:
                account_move_lines_to_reconcile |= line
        account_move_lines_to_reconcile.reconcile()

        # change the state of the expense
        expense_id.state = 'done'
        return {'type': 'ir.actions.act_window_close'}
