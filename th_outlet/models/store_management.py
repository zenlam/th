# __author__ = 'trananhdung'


from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class OutletManagement(models.Model):
    _inherit = 'stock.warehouse'

    @api.multi
    @api.depends('create_from')
    def _compute_is_outlet(self):
        for r in self:
            r.is_outlet = r.create_from == 'outlet'

    # name = fields.Char(string=_('Outlet Name'))
    # code = fields.Char(string=_('Outlet Code'))
    is_outlet = fields.Boolean(string=_('is an Outlet'), compute='_compute_is_outlet', store=True)
    create_from = fields.Selection(selection=[('outlet', _('Created from Outlet')),
                                              ('warehouse', _('Created from Warehouse'))],
                                   string=_('Create from'), default='warehouse')
    ttype = fields.Selection(selection=[('1', 'Option 1'), ('2', 'Option 2')], string=_('Outlet Type'))
    number_of_seat = fields.Integer(string=_('Number of Seat'))
    rental_percent = fields.Float(string=_('% of Rental'))
    state = fields.Selection(selection=[('open', _('Open')),
                                        ('close', _('Closed')),
                                        ('renovation', _('Under Renovation'))],
                             string=_('Status'), default='open')
    size = fields.Char(string=(_('Outlet Size')))
    analytic_account_id = fields.Many2one('account.analytic.account', string=_('Analytic Account'), required=True)
    fiscal_position_id = fields.Many2one('account.fiscal.position', string=_('Fiscal Position'))
    available_pricelist_ids = fields.Many2many('product.pricelist',
                                               'outlet_pricelist_rel',
                                               'outlet_id', 'pricelist_id',
                                               string='Available Pricelists',
                                               required=True,
                                               help="Make several pricelists "
                                                    "available for outlet.")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id,
                                 string=_('Company'), readonly=False)
    pos_config_ids = fields.One2many('pos.config', 'outlet_id', string=_('Pos Configs'))
    area_id = fields.Many2one('res.country.area', string=_('Area'))
    wholesaler = fields.Boolean(default=False, string=_('Wholesaler License'))

    # tab information
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    address = fields.Char(compute='_get_store_address', string=_('Address'), store=True)

    shipping_to_other_address = fields.Boolean(default=False, string=_('Shipping to Other Address'))
    other_street = fields.Char()
    other_street2 = fields.Char()
    other_zip = fields.Char(change_default=True)
    other_city = fields.Char()
    other_state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
    other_country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    other_address = fields.Char(compute='_get_other_address', string=_('Other Address'), store=True)

    phone = fields.Char(string=_('Phone'))
    mobile = fields.Char(string=_('Mobile'))
    fax = fields.Char(string=_('Fax'))
    email = fields.Char(string=_('Email'))

    date_open = fields.Date(string=_('Open Date'))
    date_close = fields.Date(string=_('Close Date'))
    operation_hours = fields.Selection(selection=[('standard', _('Standard Hours')),
                                                  ('24', _('24 Hours')),
                                                  ('extended', _('Extended Hours'))],
                                       string=_('Operation Hours'), default='standard')

    # tab users
    users = fields.Many2many('res.users', 'store_user_rel', string=_('Users'))
    store_managers = fields.Many2many('res.users', 'store_manager_user_rel', string=_('Outlet Managers'))
    authorizer = fields.Many2many('res.users', 'store_authorizer_user_rel', string=_('Authorizer'))

    # tab receipt
    receipt_header = fields.Html(string=_('Receipt Header'))
    receipt_footer = fields.Html(string=_('Receipt Footer'))

    _sql_constraints = [
        ('code_uniq', 'unique (code)', _("Outlet code already exists!")),
    ]

    @api.multi
    def write(self, vals):
        # update config from store to all pos.config
        # warehouse_id = vals.get('warehouse_id', None)
        receipt_header = vals.get('receipt_header', None)
        receipt_footer = vals.get('receipt_footer', None)
        authorizer = vals.get('authorizer', None)

        config_vals = {}
        # if warehouse_id is not None:
        #     warehouse = self.env['stock.warehouse'].browse(warehouse_id)
        #     config_vals['stock_location_id'] = warehouse.lot_stock_id.id
        if receipt_header is not None:
            config_vals['receipt_header'] = receipt_header
        if receipt_footer is not None:
            config_vals['receipt_footer'] = receipt_footer
        if authorizer is not None:
            config_vals['authorizer'] = authorizer

        if config_vals:
            for pos_config in self.mapped('pos_config_ids'):
                pos_config.write(config_vals)

        # save old user of store to dict
        old_store_user = {}
        old_authorizer = {}
        old_store_manager = {}
        for store in self:
            # update warehouse for user if store change warehouse
            # store.change_warehouse_user(vals)

            # get old store, authorizer, store manager before update
            if vals.get('users', False) or vals.get('store_managers', False) or vals.get('authorizer', False):
                old_store_user[store.id] = store.users
                old_authorizer[store.id] = store.authorizer
                old_store_manager[store.id] = store.store_managers

        res = super(OutletManagement, self).write(vals)

        # if vals.get('name', False) or vals.get('code', False):
        #     self.update_warehouse()

        if vals.get('users', False) or vals.get('store_managers', False) or vals.get(
                'authorizer', False):
            for store in self:
                # removed user = old user - current user
                old_store_user[store.id] = old_store_user[store.id] - store.users
                old_authorizer[store.id] = old_authorizer[store.id] - store.authorizer
                old_store_manager[store.id] = old_store_manager[store.id] - store.store_managers
            pos_user_group = self.env.ref('point_of_sale.group_pos_user')
            pos_manager_group = self.env.ref('point_of_sale.group_pos_manager')
            self.remove_user_group(old_store_user, pos_user_group)
            self.remove_user_group(old_authorizer, pos_user_group)
            self.remove_user_group(old_store_manager, pos_manager_group)
            self.update_user_group()

            # self.remove_user_warehouse(old_store_user)
            # self.remove_user_warehouse(old_authorizer)
            # self.remove_user_warehouse(old_store_manager)
            # self.update_warehouse_for_user()

        if vals.get('available_pricelist_ids', False):
            for outlet in self:
                if outlet.available_pricelist_ids:
                    default_pricelists = outlet.pos_config_ids.mapped(
                        'pricelist_id').ids
                    if not all(pricelist in outlet.available_pricelist_ids.ids
                               for pricelist in default_pricelists):
                        raise ValidationError(
                            _('You can not directly modify the '
                              'Available Pricelists,\n'
                              'First you need to check for Default Pricelist '
                              'inside POS Session(s) of current outlet.\n'
                              'As the default pricelist must be include in '
                              'the available pricelists.\n\n'
                              'List of POS Session: \n%s') %
                            ('\n'.join(
                                [session.name
                                 for session in outlet.pos_config_ids])))
        return res

    @api.model
    def create(self, vals):
        record = super(OutletManagement, self).create(vals)
        # warehouse = record.create_warehouse()
        # record.warehouse_id = warehouse.id
        # Update warehouse

        record.update_user_group()
        # record.update_warehouse_for_user()
        return record

    # @api.multi
    # def create_warehouse(self):
    #     self.ensure_one()
    #     return self.env['stock.warehouse'].create(self._prepare_warehouse_vals(self))

    # @api.multi
    # def update_warehouse(self):
    #     for store in self:
    #         store.warehouse_id.write({'name': store.name, 'code': store.code})

    # @api.model
    # def _prepare_warehouse_vals(self):
    #     default_resupply_wh_id = self.env['stock.warehouse'].search(
    #         [('company_id', '=', self.env.user.company_id.id),
    #          ('default_resupply', '=', True)], limit=1)
    #     if not default_resupply_wh_id:
    #         raise ValidationError(_('You need to have config the Default Resupply warehouse for this store to do automated create Warehouse'))
    #     return {
    #         # 'name': store.name,
    #         # 'code': store.code,
    #         'default_resupply_wh_id': default_resupply_wh_id.id,
    #         'buy_to_resupply': True,
    #         'reception_steps': 'one_step',
    #         'delivery_steps': 'ship_only',
    #     }

    @api.multi
    @api.depends('street', 'street2', 'zip', 'city', 'state_id')
    def _get_store_address(self):
        for store in self:
            add_field = [
                store.street or '',
                store.street2 or '',
                store.zip or '',
                store.city or '',
                store.state_id and store.state_id.name or '',
            ]
            address_list = filter(None, add_field)
            store.address = ', '.join(address_list)

    @api.multi
    @api.depends('other_street', 'other_street2', 'other_zip', 'other_city', 'other_state_id')
    def _get_other_address(self):
        for store in self:
            add_field = [
                store.other_street or '',
                store.other_street2 or '',
                store.other_zip or '',
                store.other_city or '',
                store.other_state_id and store.other_state_id.name or '',
            ]
            address_list = filter(None, add_field)
            store.other_address = ', '.join(address_list)

    @api.multi
    def update_user_group(self):
        user_group = self.env.ref('point_of_sale.group_pos_user')
        manager_group = self.env.ref('point_of_sale.group_pos_manager')
        for user in self.users.filtered(lambda u: user_group.id not in u.groups_id.ids):
            user.groups_id += user_group
        for user in self.authorizer.filtered(lambda u: user_group.id not in u.groups_id.ids):
            user.groups_id += user_group
        for user in self.store_managers.filtered(lambda u: manager_group.id not in u.groups_id.ids):
            user.groups_id += manager_group

    # @api.multi
    # def update_warehouse_for_user(self):
    #     for store in self:
    #         new_users = store.users
    #         new_users |= store.store_managers
    #         new_users |= store.authorizer
    #         for u in new_users:
    #             u.warehouse_ids += store

    @api.multi
    def remove_user_group(self, users, group):
        if group:
            for key, user in users.items():
                for u in user:
                    u.groups_id -= group

    # @api.multi
    # def remove_user_warehouse(self, users):
    #     for store in self:
    #         for key, user in users.items():
    #             for u in user:
    #                 u.warehouse_ids -= store

    # @api.multi
    # def change_warehouse_user(self, vals):
    #     warehouse_id = vals.get('warehouse_id', False)
    #     if warehouse_id:
    #         new_warehouse = self.env['stock.warehouse'].browse(warehouse_id)
    #         for store in self:
    #             users = self.env['res.users']
    #             users |= store.users
    #             users |= store.store_managers
    #             old_warehouse = store.warehouse_id
    #             for user in users:
    #                 if old_warehouse:
    #                     user.warehouse_ids -= old_warehouse
    #                 user.warehouse_ids += new_warehouse

    # @api.multi
    # def toggle_active_warehouse(self, active):
    #     warehouses = self.sudo().with_context(active_test=False)
    #     warehouses.write({'active': active})

    def _get_locations_values(self, vals):
        """ Update the warehouse locations.
        Note: Need to pass analytic account to the internal location creation
        """
        res = super(OutletManagement, self)._get_locations_values(vals)
        if vals.get('analytic_account_id'):
            for location, location_value in res.items():
                if location_value.get('usage') == 'internal':
                    location_value.update({
                        'account_analytic_id': vals['analytic_account_id']
                    })
        return res
