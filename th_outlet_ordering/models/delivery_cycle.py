# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from .common import DAY_OF_WEEKS
from odoo.exceptions import ValidationError


class OutletOrderingDeliveryCycle(models.Model):
    _name = 'outlet.ordering.delivery_cycle'
    _order = 'date_start'

    @api.model
    def _get_cutoff_time_1(self):
        """

        :return:
        """
        return self.env.user.company_id.outlet_ordering_cutoff_time_1

    @api.model
    def _get_cutoff_time_2(self):
        """

        :return:
        """
        return self.env.user.company_id.outlet_ordering_cutoff_time_2

    name = fields.Char(string=_('Name'), required=True)
    code = fields.Char(string=_('Delivery Code'), required=True)
    date_start = fields.Date(string=_('Date Start'), copy=False)
    date_end = fields.Date(string=_('Date End'), copy=False)
    apply_type = fields.Selection(selection=[('outlet', _('Outlet')),
                                             ('area', _('Outlet Area'))], string=_('Applied for'), required=True)
    outlet_id = fields.Many2one(comodel_name='stock.warehouse', string=_('Applied Outlet'),
                                domain=[('create_from', '=', 'outlet')])
    area_id = fields.Many2one(comodel_name='res.country.area', string=_('Applied Area'))
    company_id = fields.Many2one(comodel_name='res.company', string=_('Company'),
                                 required=True, default=lambda self: self.env.user.company_id)
    remark = fields.Text(string=_('Remark'))
    line_ids = fields.One2many(comodel_name='outlet.ordering.delivery_cycle.line', inverse_name='delivery_cycle_id',
                               string='Details', ondelete='cascade')
    cutoff_time_internal = fields.Float(string=_('Cut-off Time (Internal)'), readonly=True,
                                        related='company_id.outlet_ordering_cutoff_time_internal')
    cutoff_time_1 = fields.Float(string=_('Ordering Cut-off Time (HAVI)'), readonly=True,
                                 related='company_id.outlet_ordering_cutoff_time_1')
    cutoff_time_2 = fields.Float(string=_('2nd Cut-off Time (HAVI)'), readonly=True,
                                 related='company_id.outlet_ordering_cutoff_time_2')

    _sql_constraints = [
        ('date_range_check', 'check (date_start <= date_end)',
         _('End date cannot earlier than start date')),
        ('cutoff_time_check', 'check (cutoff_time_1 < cutoff_time_2)',
         _('2nd Cut-off time must be larger than 1st Cut-off time')),
    ]

    def _check_date_range(self):
        """

        :return:
        """
        where_clause = ''
        conditions = []
        conditions.append('id != %s' % self.id)
        conditions.append("apply_type = '%s'" % self.apply_type)
        if self.apply_type == 'outlet':
            conditions.append('outlet_id = %s' % self.outlet_id.id)
        else:
            conditions.append('area_id = %s' % self.area_id.id)

        date_condition = []
        if self.date_start:
            date_condition.append("(date_end IS NOT NULL AND date_end < '%s'::date)" % self.date_start)
        if self.date_end:
            date_condition.append("(date_start IS NOT NULL AND date_start > '%s'::date)" % self.date_end)
        if date_condition:
            conditions.append('NOT (%s)' % ' OR '.join(date_condition))

        where_clause += ' AND '.join(conditions)
        sql = 'SELECT "name" FROM {table} WHERE {where_clause}'.format(table=self._table, where_clause=where_clause)
        self.env.cr.execute(sql)
        names = self.env.cr.fetchall()
        if names:
            raise ValidationError(_('There is already a delivery cycle for selected outlet within this date range: '
                                    '{cycles}, please check again!').format(
                cycles=', '.join([i[0] for i in names])))
        return True

    @api.constrains('date_start', 'date_end', 'area_id', 'outlet_id', 'apply_type')
    def constraint_date_range(self):
        for r in self:
            return r._check_date_range()

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        """

        :param args:
        :param offset:
        :param limit:
        :param order:
        :param count:
        :param access_rights_uid:
        :return:
        """
        if args is None:
            args = []
        outlet_id = self.env.context.get('outlet_id', False)
        if outlet_id:
            args.append(('outlet_id', '=', outlet_id))
        return super(OutletOrderingDeliveryCycle, self)._search(
            args=args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid
        )


class OutletOrderingDeliveryCycleDetails(models.Model):
    _name = 'outlet.ordering.delivery_cycle.line'

    delivery_cycle_id = fields.Many2one(comodel_name='outlet.ordering.delivery_cycle', required=True)
    delivery_day = fields.Selection(selection=DAY_OF_WEEKS, required=True, string=_('Delivery Day'))
    cutoff_day = fields.Selection(selection=DAY_OF_WEEKS, required=True, string=_('Cut-off Day'))
    cutoff_time_internal = fields.Float(string=_('Cut-off Time (Internal)'),
                                        related='delivery_cycle_id.cutoff_time_internal')
    cutoff_time_1 = fields.Float(string=_('Ordering Cut-off Time (HAVI)'), related='delivery_cycle_id.cutoff_time_1')
    cutoff_time_2 = fields.Float(string=_('2nd Cut-off Time (HAVI)'), related='delivery_cycle_id.cutoff_time_2')

    _sql_constraints = [
        ('delivery_cycle_uniq', 'unique (delivery_cycle_id, delivery_day)',
         _('Delivery Day must be unique for each Delivery Cycle configuration'))
    ]
