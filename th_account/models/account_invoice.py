# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    account_analytic_id = fields.Many2one(required=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            return super(AccountInvoiceLine, self.with_context(product_tmpl_id=self.product_id.product_tmpl_id.id
                                                               ))._onchange_product_id()
        else:
            return super(AccountInvoiceLine, self)._onchange_product_id()

    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        if self.uom_id and self.product_id:
            return super(AccountInvoiceLine, self.with_context(product_tmpl_id=self.product_id.product_tmpl_id.id
                                                               ))._onchange_uom_id()
        else:
            return super(AccountInvoiceLine, self)._onchange_uom_id()



class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    account_analytic_id = fields.Many2one('account.analytic.account',
                                          string='Analytic Account',
                                          required=True)

    @api.multi
    def action_move_create(self):
        """ Creates invoice related analytics and financial move lines.
        Note: This function will create accounting entry when validating an invoice. Need to override the function due
        to the creation is in the middle.
        """
        account_move = self.env['account.move']

        for inv in self:
            if not inv.journal_id.sequence_id:
                raise UserError(_(
                    'Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line_ids.filtered(lambda line: line.account_id):
                raise UserError(_('Please add at least one invoice line.'))
            if inv.move_id:
                continue

            if not inv.date_invoice:
                inv.write({'date_invoice': fields.Date.context_today(self)})
            if not inv.date_due:
                inv.write({'date_due': inv.date_invoice})
            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and analytic lines)
            iml = inv.invoice_line_move_line_get()
            iml += inv.tax_line_move_line_get()

            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.compute_invoice_totals(
                company_currency, iml)

            name = inv.name or ''
            if inv.payment_term_id:
                totlines = \
                    inv.payment_term_id.with_context(
                        currency_id=company_currency.id).compute(total,
                                                                 inv.date_invoice)[
                        0]
                res_amount_currency = total_currency
                for i, t in enumerate(totlines):
                    if inv.currency_id != company_currency:
                        amount_currency = company_currency._convert(t[1],
                                                                    inv.currency_id,
                                                                    inv.company_id,
                                                                    inv._get_currency_rate_date() or fields.Date.today())
                    else:
                        amount_currency = False

                    # last line: add the diff
                    res_amount_currency -= amount_currency or 0
                    if i + 1 == len(totlines):
                        amount_currency += res_amount_currency

                    # need to assign analytic account from invoice to the move line
                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': inv.account_id.id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency and amount_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'invoice_id': inv.id,
                        'account_analytic_id': inv.account_analytic_id.id,
                    })
            else:
                # need to assign analytic account from invoice to the move line
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': inv.account_id.id,
                    'date_maturity': inv.date_due,
                    'amount_currency': diff_currency and total_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'invoice_id': inv.id,
                    'account_analytic_id': inv.account_analytic_id.id,
                })
            part = self.env['res.partner']._find_accounting_partner(
                inv.partner_id)
            line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
            line = inv.group_lines(iml, line)

            line = inv.finalize_invoice_move_lines(line)

            date = inv.date or inv.date_invoice
            move_vals = {
                'ref': inv.reference,
                'line_ids': line,
                'journal_id': inv.journal_id.id,
                'date': date,
                'narration': inv.comment,
            }
            move = account_move.create(move_vals)
            # Pass invoice in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move.post(invoice=inv)
            # make the invoice point to that move
            vals = {
                'move_id': move.id,
                'date': date,
                'move_name': move.name,
            }
            inv.write(vals)
        return True

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None,
                        description=None, journal_id=None):
        """ Prepare the dict of values to create the new credit note from the invoice.
        Note: Create the credit note from invoice (Customer Invoice, Vendor Bill) with analytic account.
        """
        res = super(AccountInvoice, self)._prepare_refund(invoice,
                                                          date_invoice, date,
                                                          description,
                                                          journal_id)
        res.update({
            'account_analytic_id': invoice.account_analytic_id.id,
        })
        return res


class AccountInvoiceTax(models.Model):
    _inherit = "account.invoice.tax"

    account_analytic_id = fields.Many2one(required=True)
