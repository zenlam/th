# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class HrExpense(models.Model):
    _inherit = "hr.expense"

    analytic_account_id = fields.Many2one(required=1)
    expense_category_id = fields.Many2one('th.expense.category',
                                          string="Expense Category",
                                          required=True)
    is_double_validation = fields.Boolean(
        compute='_compute_is_double_validation',
        default=False
    )
    date = fields.Date(default=None)
    actual_date = fields.Date(string="Actual Date", required=True)
    show_base_currency = fields.Boolean(string="Show Base Currency",
                                        compute='_check_base_currency')
    base_currency_id = fields.Many2one(
        'res.currency', string="Base Currency", store=True,
        default=lambda self: self.env.user.company_id.currency_id
    )
    base_currency_total = fields.Monetary(
        string="Total (Base Currency)", readony=True,
        currency_field='base_currency_id',
        compute='_compute_base_currency_total',
        store=True
    )
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('reported', 'Submitted'),
        ('validated', 'Validated'),
        ('approved', 'Approved'),
        ('posted', 'Posted'),
        ('done', 'Paid'),
        ('refused', 'Refused')
    ], compute='', string='Status', copy=False, index=True, readonly=True,
        store=True, help="Status of the expense.",
        default='draft', track_visibility='onchange')

    @api.model
    def get_email_to(self):
        # get email of all Finance groups of Expenses for mail template
        users = self.env.ref('hr_expense.group_hr_expense_manager').users
        finance_users = self.env['hr.employee'].search([
            ('user_id.id', 'in', users.ids)
        ])
        email_list = [
            user.work_email for user in finance_users if user.work_email]
        return ", ".join(email_list)

    @api.multi
    def refuse_expense(self, reason):
        if False:
            super(HrExpense, self).refuse_expense(reason)
        self.write({'is_refused': True})
        self.sheet_id.write({'state': 'cancel'})
        self.write({'state': 'refused'})
        self.message_post_with_view(
            'hr_expense.hr_expense_template_refuse_reason',
            values={'reason': reason, 'is_sheet': False, 'name': self.name})
        self.activity_update()

    @api.multi
    def action_reset_expense(self):
        for expense in self:
            obj = expense.sheet_id
            if self.user_has_groups('hr_expense.group_hr_expense_user') or \
                    expense.employee_id.user_id == self.env.context.get('uid'):
                obj.reset_expense_sheets()
                expense.write({'state': 'draft'})
            expense.activity_update()

    @api.multi
    def _compute_is_double_validation(self):
        for expense in self:
            if expense.employee_id.parent_id and \
                    expense.employee_id.head_of_manager_id:
                expense.is_double_validation = True
            elif expense.expense_category_id.is_double_validation is True:
                if expense.base_currency_total >= \
                        expense.expense_category_id.amount:
                    expense.is_double_validation = True

    @api.multi
    def action_post_journal_entries(self):
        for expense in self:
            obj = expense.sheet_id
            obj.action_sheet_move_create()
            if expense.payment_mode == 'own_account':
                expense.write({'state': 'posted'})
            else:
                expense.write({'state': 'done'})

    @api.multi
    def action_validate_expense(self):
        for expense in self:
            if self.env.context.get('uid') != \
                    expense.employee_id.parent_id.user_id.id:
                raise ValidationError(_(
                    "Only manager of %s has the right to approve this expense."
                ) % expense.employee_id.name)
            if expense.is_double_validation is True:
                # send email to employees in Expense - Finance group
                if expense.base_currency_total >= \
                        expense.expense_category_id.amount:
                    expense_template = self.env.ref(
                        'th_hr_expense.email_template_finance_approve_required'
                    )
                    expense_template.send_mail(expense.id, force_send=True)
                expense.write({'state': 'validated'})
            expense.activity_update()

    @api.multi
    def action_approve_expense(self):
        for expense in self:
            if expense.is_double_validation is False:
                if self.env.context.get('uid') != \
                        expense.employee_id.parent_id.user_id.id:
                    raise ValidationError(_(
                        "Only manager of %s has the right to approve "
                        "this expense."
                    ) % expense.employee_id.name)
            else:  # is_double_validation is True:
                if expense.expense_category_id.is_double_validation is True \
                        and expense.base_currency_total >= \
                        expense.expense_category_id.amount:
                    if not self.user_has_groups(
                            'hr_expense.group_hr_expense_manager'):
                        raise ValidationError(_(
                            "Claim amount exceeded limit. Only finance can "
                            "approve this expense."
                        ))
                else:
                    if self._context.get('uid') != \
                            expense.employee_id.head_of_manager_id.id:
                        raise ValidationError(_(
                            "Only head of manager of %s has the right "
                            "to approve this expense."
                        ) % expense.employee_id.name)
            obj = expense.sheet_id
            obj.approve_expense_sheets()
            expense.write({'state': 'approved'})
            expense.activity_update()

    @api.multi
    def action_submit_expense_to_manager(self):
        self.date = (datetime.now() + timedelta(hours=8)).date()
        if self.actual_date:
            day_passed = (self.date - self.actual_date).days + 1
            if day_passed > self.expense_category_id.claim_valid_days:
                raise ValidationError('The claim date has exceeded the '
                                      'validity days for this claim type, '
                                      'please create requests which are within'
                                      ' valid claim days.')
        if self.expense_category_id.is_require_attachment is True and \
                self.attachment_number < 1:
            raise ValidationError('This claim type requires an attachment, '
                                  'please attach receipt to proceed.')
        if not self.sheet_id:
            vals = {
                'name': self.name,
                'employee_id': self.employee_id.id,
                'expense_line_ids': [(4, self.id)]
            }
            obj = self.env['hr.expense.sheet'].create(vals)
            obj._onchange_employee_id()
            obj.action_submit_sheet()
        else:
            obj = self.sheet_id
            obj.action_submit_sheet()
        self.write({'state': 'reported'})
        self.activity_update()

    @api.depends('total_amount', 'currency_id')
    def _compute_base_currency_total(self):
        for expense in self:
            if expense.currency_id:
                amount = expense.currency_id._convert(
                    expense.total_amount, expense.base_currency_id,
                    expense.company_id, expense.date or fields.Date.today())
                expense.base_currency_total = amount

    @api.depends('currency_id')
    def _check_base_currency(self):
        if self.currency_id != self.env.user.company_id.currency_id:
            self.show_base_currency = True
        else:
            self.show_base_currency = False

    @api.multi
    def _get_account_move_line_values(self):
        """ Create move lines based on the expense
        Note: This function will create move lines when the user post journal entries in hr expense.
        """
        res = super(HrExpense, self)._get_account_move_line_values()
        for expense, move_lines in res.items():
            for line in move_lines:
                expense_id = self.env['hr.expense'].browse(expense)
                if not line.get('analytic_account_id'):
                    line.update({
                        'analytic_account_id': expense_id.analytic_account_id.id,
                    })
        return res

    def _get_responsible_for_approval(self):
        if self.employee_id.parent_id.user_id:
            return self.employee_id.parent_id.user_id
        elif self.employee_id.head_of_manager_id.user_id:
            return self.employee_id.head_of_manager_id.user_id
        return self.env['res.users']

    def activity_update(self):
        for expense in self.filtered(lambda exp: exp.state == 'reported'):
            self.activity_schedule(
                'th_hr_expense.mail_action_expense_approval',
                user_id=expense.sudo()._get_responsible_for_approval().id or self.env.user.id
            )
        self.filtered(lambda exp: exp.state == 'approved').activity_feedback(
            ['th_hr_expense.mail_action_expense_approval']
        )
        self.filtered(lambda exp: exp.state == 'refused').activity_unlink(
            ['th_hr_expense.mail_action_expense_approval']
        )


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    @api.multi
    def _track_subtype(self, init_values):
        """
        NOTE: disable this function to avoid confusion
        """
        if False:
            super(HrExpenseSheet, self)._track_subtype()

    def activity_update(self):
        """
        NOTE: disable the activity update for expense report to avoid
        confusion because TH is using expense instead of expense report
        """
        if False:
            super(HrExpenseSheet, self).activity_update()
