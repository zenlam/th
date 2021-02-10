# __author__ = 'trananhdung'


from odoo import models, api
from odoo import SUPERUSER_ID


class BaseModelExtend(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def get_need_models_check_by_store(self):
        return ['stock.warehouse', 'pos.config']

    @api.model
    @api.returns('self',
                 upgrade=lambda self, value, args, offset=0, limit=None, order=None,
                                count=False: value if count else self.browse(value),
                 downgrade=lambda self, value, args, offset=0, limit=None, order=None,
                                  count=False: value if count else value.ids)
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
        override search function of Model to pass all rule with user have see_all = True
        :param args:
        :param offset:
        :param limit:
        :param order:
        :param count:
        :return:
        """
        if not args:
            args = []
        args += self.get_domain_filter_by_store(self.get_need_models_check_by_store())
        return super(BaseModelExtend, self).search(args, offset, limit, order, count=count)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if not domain:
            domain = []
        domain += self.get_domain_filter_by_store(self.get_need_models_check_by_store())
        return super(BaseModelExtend, self).read_group(domain, fields, groupby, offset=offset,
                                                       limit=limit, orderby=orderby, lazy=lazy)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []
        args += self.get_domain_filter_by_store(self.get_need_models_check_by_store())
        return super(BaseModelExtend, self).name_search(name, args, operator, limit)

    @api.model
    def get_domain_filter_by_store(self, check_models):
        """

        :param check_models: list model name need to check
        :return:
        """
        domain = []
        if self._uid == SUPERUSER_ID or self.env.context.get('pass_store_rule', False):
            return domain
        if self._name in check_models:
            if not self.env.user.see_all:
                ls_stores = self.env.user.with_context(active_test=False).other_outlet_ids
                if self.env.user.has_group('point_of_sale.group_pos_user') or \
                        self.env.user.has_group('point_of_sale.group_pos_manager'):
                    ls_stores |= self.env.user.with_context(active_test=False).user_outlet_ids
                    ls_stores |= self.env.user.with_context(active_test=False).manager_outlet_ids
                if self._name == 'stock.warehouse':
                    domain += [('id', 'in', ls_stores.ids or [-1])]
                else:
                    domain += [('outlet_id', 'in', ls_stores.ids or [-1])]
        return domain
