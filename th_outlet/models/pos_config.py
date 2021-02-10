# __author__ = 'trananhdung'

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = 'pos.config'

    @api.depends('outlet_id.available_pricelist_ids')
    def _compute_pricelists(self):
        for rec in self:
            if rec.outlet_id:
                rec.available_pricelist_ids = [
                    (6, 0, rec.outlet_id.available_pricelist_ids.ids)]

    outlet_id = fields.Many2one('stock.warehouse', string=_('Outlet'),
                                domain=[('create_from', '=', 'outlet')], required=True)
    address = fields.Char(compute="_get_address", readonly=1, store=True)
    outlet_street = fields.Char(related='outlet_id.street', store=True)
    outlet_street2 = fields.Char(related='outlet_id.street2', store=True)
    outlet_zip = fields.Char(related='outlet_id.zip', store=True)
    outlet_city = fields.Char(related='outlet_id.city', store=True)
    outlet_state_name = fields.Char(related='outlet_id.state_id.name', store=True)
    outlet_country_name = fields.Char(related='outlet_id.country_id.name', store=True)
    outlet_mobile = fields.Char(related='outlet_id.mobile', store=True)
    phone = fields.Char(related='outlet_id.phone', string=_('Phone'), readonly=1, store=True)
    fax = fields.Char(related='outlet_id.fax', string=_('Fax'), readonly=1, store=True)
    receipt_footer = fields.Html(string=_('Receipt Footer'))
    authorizer = fields.Many2many('res.users', 'pos_config_authorizer_user_rel',
                                  string=_('Authorizer'))
    pricelist_id = fields.Many2one(default=None)
    available_pricelist_ids = fields.Many2many(compute="_compute_pricelists",
                                               store=True)

    # Override method & put logic(same as base, no change) inside for-loop
    @api.constrains('pricelist_id', 'available_pricelist_ids', 'journal_id',
                    'invoice_journal_id', 'journal_ids')
    def _check_currencies(self):
        for rec in self:
            # -----------------------------------------------------------------
            # This validation part was transfer inside `write` method of Outlet
            # -----------------------------------------------------------------
            # if rec.pricelist_id not in rec.available_pricelist_ids:
            #     raise ValidationError(_(
            #         "The default pricelist must be included in "
            #         "the available pricelists."))
            if any(rec.available_pricelist_ids.mapped(
                    lambda pricelist:
                    pricelist.currency_id != rec.currency_id)):
                raise ValidationError(_(
                    "All available pricelists must be in the same "
                    "currency as the company or "
                    "as the Sales Journal set on this point of "
                    "sale if you use the Accounting application."))
            if rec.invoice_journal_id.currency_id and \
                    rec.invoice_journal_id.currency_id != rec.currency_id:
                raise ValidationError(_(
                    "The invoice journal must be in the same currency as "
                    "the Sales Journal or the company currency "
                    "if that is not set."))
            if any(rec.journal_ids.mapped(
                    lambda journal: rec.currency_id not in (
                    journal.company_id.currency_id, journal.currency_id))):
                raise ValidationError(_(
                    "All payment methods must be in the same currency as "
                    "the Sales Journal or the company currency "
                    "if that is not set."))

    # Override method & put logic(same as base, no change) inside for-loop
    @api.constrains('company_id', 'available_pricelist_ids')
    def _check_companies(self):
        for rec in self:
            if any(rec.available_pricelist_ids.mapped(
                    lambda pl: pl.company_id.id not in (
                    False, rec.company_id.id))):
                raise ValidationError(_(
                    "The selected pricelists must belong to no company or "
                    "the company of the point of sale."))

    @api.onchange('outlet_id')
    def onchange_outlet_id(self):
        store = self.outlet_id
        if store:
            self.authorizer = store.authorizer
            self.stock_location_id = self.outlet_id.lot_stock_id
            self.use_pricelist = True

    @api.multi
    @api.depends('outlet_id', 'outlet_id.address', 'outlet_id.company_id')
    def _get_address(self):
        for config in self:
            config.address = config.outlet_id.address or ''
            if not config.address:
                company = config.outlet_id.company_id
                add_field = [
                    company.street or '',
                    company.street2 or '',
                    company.city or '',
                    company.state_id and company.state_id.name or '',
                 ]
                address_list = filter(None, add_field)
                config.address = ', '.join(address_list)
