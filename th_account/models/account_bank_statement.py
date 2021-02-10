# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, pycompat
from odoo.exceptions import UserError, ValidationError


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    def counterpart_prepare_payment_vals(self, st_line):
        """ This will return the payment values dictionary to function
        fast_counterpart_creation.
        """
        account_type_receivable = \
            self.env.ref('account.data_account_type_receivable')
        total = st_line.amount
        payment_methods = (total > 0) and \
                          st_line.journal_id.inbound_payment_method_ids or \
                          st_line.journal_id.outbound_payment_method_ids
        currency = st_line.journal_id.currency_id or \
                   st_line.company_id.currency_id
        partner_type = 'customer' \
            if st_line.account_id.user_type_id == account_type_receivable \
            else 'supplier'
        return {
            'payment_method_id': payment_methods and payment_methods[
                0].id or False,
            'payment_type': total > 0 and 'inbound' or 'outbound',
            'partner_id': st_line.partner_id.id,
            'partner_type': partner_type,
            'journal_id': st_line.statement_id.journal_id.id,
            'payment_date': st_line.date,
            'state': 'reconciled',
            'currency_id': currency.id,
            'amount': abs(total),
            'communication': st_line._get_communication(
                payment_methods[0] if payment_methods else False),
            'name': st_line.statement_id.name or _(
                "Bank Statement %s") % st_line.date,
            'analytic_account_id': st_line.statement_id.pos_session_id.config_id.outlet_id.analytic_account_id.id,
        }

    def prepare_account_move_line(self, st_line):
        """ This will return the journal item values dictionary to function
            fast_counterpart_creation.
        """
        return {
            'name': st_line.name,
            'debit': st_line.amount < 0 and -st_line.amount or 0.0,
            'credit': st_line.amount > 0 and st_line.amount or 0.0,
            'account_id': st_line.account_id.id,
            'partner_id': st_line.partner_id.id,
            'statement_line_id': st_line.id,
            'analytic_account_id': st_line.statement_id.pos_session_id.config_id.outlet_id.analytic_account_id.id,
        }

    def _prepare_reconciliation_move_line(self, move, amount):
        """ Prepare the dict of values to balance the move. This function will
        return account move line dictionary values to function
        fast_counterpart_creation.
        """
        res = super(AccountBankStatementLine, self)._prepare_reconciliation_move_line(move, amount)
        res.update({
            'analytic_account_id': self.statement_id.pos_session_id.config_id.outlet_id.analytic_account_id.id,
        })
        return res

    @api.multi
    def fast_counterpart_creation(self):
        """This function is called when confirming a bank statement and will allow to automatically process lines without
        going in the bank reconciliation widget. By setting an account_id on bank statement lines, it will create a journal
        entry using that account to counterpart the bank account
        Note: Need to override the whole function due to the payment is created
        in the middle of the function
        """
        payment_list = []
        move_list = []

        already_done_stmt_line_ids = [a['statement_line_id'][0] for a in
                                      self.env['account.move.line'].read_group(
                                          [('statement_line_id', 'in',
                                            self.ids)], ['statement_line_id'],
                                          ['statement_line_id'])]
        managed_st_line = []
        for st_line in self:
            # Technical functionality to automatically reconcile by creating a new move line
            if st_line.account_id and not st_line.id in already_done_stmt_line_ids:
                managed_st_line.append(st_line.id)
                payment_list.append(self.counterpart_prepare_payment_vals(st_line))
                # Create move and move line vals
                move_vals = st_line._prepare_reconciliation_move(
                    st_line.statement_id.name)
                aml_dict = self.prepare_account_move_line(st_line)
                st_line._prepare_move_line_for_currency(aml_dict,
                                                        st_line.date or fields.Date.context_today())
                move_vals['line_ids'] = [(0, 0, aml_dict)]
                balance_line = self._prepare_reconciliation_move_line(
                    move_vals,
                    -aml_dict['debit'] if st_line.amount < 0 else aml_dict[
                        'credit'])
                move_vals['line_ids'].append((0, 0, balance_line))
                move_list.append(move_vals)

        # Creates
        payment_ids = self.env['account.payment'].create(payment_list)
        for payment_id, move_vals in pycompat.izip(payment_ids, move_list):
            for line in move_vals['line_ids']:
                line[2]['payment_id'] = payment_id.id
        move_ids = self.env['account.move'].create(move_list)
        move_ids.post()

        for move, st_line, payment in pycompat.izip(move_ids, self.browse(
                managed_st_line), payment_ids):
            st_line.write({'move_name': move.name})
            payment.write({'payment_reference': move.name})

    def reconcile_prepare_payment_vals(self, payment_methods, total,
                                       partner_id, partner_type, currency):
        """ This will return the payment values dictionary to function
        process_reconciliation.
        """
        return {
            'payment_method_id': payment_methods and payment_methods[0].id or False,
            'payment_type': total > 0 and 'inbound' or 'outbound',
            'partner_id': partner_id.id,
            'partner_type': partner_type,
            'journal_id': self.statement_id.journal_id.id,
            'payment_date': self.date,
            'state': 'reconciled',
            'currency_id': currency.id,
            'amount': abs(total),
            'communication': self._get_communication(payment_methods[0] if payment_methods else False),
            'name': self.statement_id.name or _("Bank Statement %s") % self.date,
            'analytic_account_id': self.statement_id.pos_session_id.config_id.outlet_id.analytic_account_id.id,
        }

    def process_reconciliation(self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None):
        """ Match statement lines with existing payments (eg. checks) and/or payables/receivables (eg. invoices and credit notes) and/or new move lines (eg. write-offs).
            If any new journal item needs to be created (via new_aml_dicts or counterpart_aml_dicts), a new journal entry will be created and will contain those
            items, as well as a journal item for the bank statement line.
            Finally, mark the statement line as reconciled by putting the matched moves ids in the column journal_entry_ids.
        Note: Create 'prepare' function to provide dictionary values to be used in this function so the 'prepare'
        function can be inherited in future.
        """
        payable_account_type = self.env.ref('account.data_account_type_payable')
        receivable_account_type = self.env.ref('account.data_account_type_receivable')
        counterpart_aml_dicts = counterpart_aml_dicts or []
        payment_aml_rec = payment_aml_rec or self.env['account.move.line']
        new_aml_dicts = new_aml_dicts or []

        aml_obj = self.env['account.move.line']

        company_currency = self.journal_id.company_id.currency_id
        statement_currency = self.journal_id.currency_id or company_currency
        st_line_currency = self.currency_id or statement_currency

        counterpart_moves = self.env['account.move']

        # Check and prepare received data
        if any(rec.statement_id for rec in payment_aml_rec):
            raise UserError(_('A selected move line was already reconciled.'))
        for aml_dict in counterpart_aml_dicts:
            if aml_dict['move_line'].reconciled:
                raise UserError(_('A selected move line was already reconciled.'))
            if isinstance(aml_dict['move_line'], pycompat.integer_types):
                aml_dict['move_line'] = aml_obj.browse(aml_dict['move_line'])

        account_types = self.env['account.account.type']
        for aml_dict in (counterpart_aml_dicts + new_aml_dicts):
            if aml_dict.get('tax_ids') and isinstance(aml_dict['tax_ids'][0], pycompat.integer_types):
                # Transform the value in the format required for One2many and Many2many fields
                aml_dict['tax_ids'] = [(4, id, None) for id in aml_dict['tax_ids']]

            user_type_id = self.env['account.account'].browse(aml_dict.get('account_id')).user_type_id
            if user_type_id in [payable_account_type, receivable_account_type] and user_type_id not in account_types:
                account_types |= user_type_id
        if any(line.journal_entry_ids for line in self):
            raise UserError(_('A selected statement line was already reconciled with an account move.'))

        # Fully reconciled moves are just linked to the bank statement
        total = self.amount
        currency = self.currency_id or statement_currency
        for aml_rec in payment_aml_rec:
            balance = aml_rec.amount_currency if aml_rec.currency_id else aml_rec.balance
            aml_currency = aml_rec.currency_id or aml_rec.company_currency_id
            total -= aml_currency._convert(balance, currency, aml_rec.company_id, aml_rec.date)
            aml_rec.with_context(check_move_validity=False).write({'statement_line_id': self.id})
            counterpart_moves = (counterpart_moves | aml_rec.move_id)
            if aml_rec.journal_id.post_at_bank_rec and aml_rec.payment_id and aml_rec.move_id.state == 'draft':
                # In case the journal is set to only post payments when performing bank
                # reconciliation, we modify its date and post it.
                aml_rec.move_id.date = self.date
                aml_rec.payment_id.payment_date = self.date
                aml_rec.move_id.post()
                # We check the paid status of the invoices reconciled with this payment
                for invoice in aml_rec.payment_id.reconciled_invoice_ids:
                    self._check_invoice_state(invoice)

        # Create move line(s). Either matching an existing journal entry (eg. invoice), in which
        # case we reconcile the existing and the new move lines together, or being a write-off.
        if counterpart_aml_dicts or new_aml_dicts:
            st_line_currency = self.currency_id or statement_currency
            st_line_currency_rate = self.currency_id and (self.amount_currency / self.amount) or False

            # Create the move
            self.sequence = self.statement_id.line_ids.ids.index(self.id) + 1
            move_vals = self._prepare_reconciliation_move(self.statement_id.name)
            move = self.env['account.move'].create(move_vals)
            counterpart_moves = (counterpart_moves | move)

            # Create The payment
            payment = self.env['account.payment']
            partner_id = self.partner_id or (aml_dict.get('move_line') and aml_dict['move_line'].partner_id) or \
                         self.env['res.partner']
            if abs(total) > 0.00001:
                partner_type = False
                if partner_id and len(account_types) == 1:
                    partner_type = 'customer' if account_types == receivable_account_type else 'supplier'
                if partner_id and not partner_type:
                    if total < 0:
                        partner_type = 'supplier'
                    else:
                        partner_type = 'customer'

                payment_methods = (total > 0) and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
                currency = self.journal_id.currency_id or self.company_id.currency_id
                payment_vals = self.reconcile_prepare_payment_vals(payment_methods, total, partner_id, partner_type, currency)
                payment = self.env['account.payment'].create(payment_vals)

            # Complete dicts to create both counterpart move lines and write-offs
            to_create = (counterpart_aml_dicts + new_aml_dicts)
            company = self.company_id
            date = self.date or fields.Date.today()
            for aml_dict in to_create:
                aml_dict['move_id'] = move.id
                aml_dict['partner_id'] = self.partner_id.id
                aml_dict['statement_line_id'] = self.id
                if st_line_currency.id != company_currency.id:
                    aml_dict['amount_currency'] = aml_dict['debit'] - aml_dict['credit']
                    aml_dict['currency_id'] = st_line_currency.id
                    if self.currency_id and statement_currency.id == company_currency.id and st_line_currency_rate:
                        # Statement is in company currency but the transaction is in foreign currency
                        aml_dict['debit'] = company_currency.round(aml_dict['debit'] / st_line_currency_rate)
                        aml_dict['credit'] = company_currency.round(aml_dict['credit'] / st_line_currency_rate)
                    elif self.currency_id and st_line_currency_rate:
                        # Statement is in foreign currency and the transaction is in another one
                        aml_dict['debit'] = statement_currency._convert(aml_dict['debit'] / st_line_currency_rate,
                                                                        company_currency, company, date)
                        aml_dict['credit'] = statement_currency._convert(aml_dict['credit'] / st_line_currency_rate,
                                                                         company_currency, company, date)
                    else:
                        # Statement is in foreign currency and no extra currency is given for the transaction
                        aml_dict['debit'] = st_line_currency._convert(aml_dict['debit'], company_currency, company,
                                                                      date)
                        aml_dict['credit'] = st_line_currency._convert(aml_dict['credit'], company_currency, company,
                                                                       date)
                elif statement_currency.id != company_currency.id:
                    # Statement is in foreign currency but the transaction is in company currency
                    prorata_factor = (aml_dict['debit'] - aml_dict['credit']) / self.amount_currency
                    aml_dict['amount_currency'] = prorata_factor * self.amount
                    aml_dict['currency_id'] = statement_currency.id

            # Create write-offs
            for aml_dict in new_aml_dicts:
                aml_dict['payment_id'] = payment and payment.id or False
                aml_obj.with_context(check_move_validity=False).create(aml_dict)

            # Create counterpart move lines and reconcile them
            for aml_dict in counterpart_aml_dicts:
                if aml_dict['move_line'].payment_id:
                    aml_dict['move_line'].write({'statement_line_id': self.id})
                if aml_dict['move_line'].partner_id.id:
                    aml_dict['partner_id'] = aml_dict['move_line'].partner_id.id
                aml_dict['account_id'] = aml_dict['move_line'].account_id.id
                aml_dict['payment_id'] = payment and payment.id or False

                counterpart_move_line = aml_dict.pop('move_line')
                new_aml = aml_obj.with_context(check_move_validity=False).create(aml_dict)

                (new_aml | counterpart_move_line).reconcile()

                self._check_invoice_state(counterpart_move_line.invoice_id)

            # Balance the move
            st_line_amount = -sum([x.balance for x in move.line_ids])
            aml_dict = self._prepare_reconciliation_move_line(move, st_line_amount)
            aml_dict['payment_id'] = payment and payment.id or False
            aml_obj.with_context(check_move_validity=False).create(aml_dict)

            move.post()
            # record the move name on the statement line to be able to retrieve it in case of unreconciliation
            self.write({'move_name': move.name})
            payment and payment.write({'payment_reference': move.name})
        elif self.move_name:
            raise UserError(_(
                'Operation not allowed. Since your statement line already received a number (%s), you cannot reconcile it entirely with existing journal entries otherwise it would make a gap in the numbering. You should book an entry and make a regular revert of it in case you want to cancel it.') % (
                                self.move_name))

        # create the res.partner.bank if needed
        if self.account_number and self.partner_id and not self.bank_account_id:
            # Search bank account without partner to handle the case the res.partner.bank already exists but is set
            # on a different partner.
            bank_account = self.env['res.partner.bank'].search([('acc_number', '=', self.account_number)])
            if not bank_account:
                bank_account = self.env['res.partner.bank'].create({
                    'acc_number': self.account_number, 'partner_id': self.partner_id.id
                })
            self.bank_account_id = bank_account

        counterpart_moves.assert_balanced()
        return counterpart_moves