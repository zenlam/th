# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-
from nacl.public import PublicKey

from odoo import fields, models, api, _

WEEKDAYS = [('0', _('Monday')),
            ('1', _('Tuesday')),
            ('2', _('Wednesday')),
            ('3', _('Thursday')),
            ('4', _('Friday')),
            ('5', _('Saturday')),
            ('6', _('Sunday'))]


class PurchaseDeliveryCyle(models.Model):
    _name = 'purchase.request.delivery.cycle'

    name = fields.Char(string=_('Name'), required=True)
    code = fields.Char(string=_('Delivery Code'), required=True)
    date_start = fields.Date(string=_('Date Start'), copy=False)
    date_end = fields.Date(string=_('Date End'), copy=False)
    apply_type = fields.Selection(selection=[('outlet', _('Outlet')),
                                             ('area', _('Outlet Area'))], string=_('Applied for'), required=True)
    outlet_ids = fields.Many2many(comodel_name='stock.warehouse',
                                  relation='purchase_request_delivery_cycle_outlet_rel',
                                  column1='delivery_cycle_id', column2='outlet_id',
                                  string=_('Applied Outlets'),
                                  domain=[('create_from', '=', 'outlet')])
    area_ids = fields.Many2many(comodel_name='res.country.area',
                                relation='purchase_request_delivery_cycle_outlet_area_rel',
                                column1='delivery_cycle_id', column2='area_id',
                                string=_('Applied Area'))
    vendor_id = fields.Many2one(comodel_name='res.partner', domain=[('supplier', '=', True)])
    company_id = fields.Many2one(comodel_name='res.company', string=_('Company'),
                                 required=True, default=lambda self: self.env.user.company_id)
    remark = fields.Text(string=_('Remark'))
    line_ids = fields.One2many(comodel_name='purchase.request.delivery.cycle.line', inverse_name='delivery_cycle_id',
                               string='Details', ondelete='cascade')
    cutoff_time = fields.Float(string=_('Cut-off Time'), required=True)

    _sql_constraints = [
        ('date_range_check', 'check (date_start <= date_end)',
         _('End date cannot earlier than start date')),
    ]

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
            sql = """
            select rel.delivery_cycle_id as delivery_cycle_id
            from purchase_request_delivery_cycle_outlet_rel as rel 
            where rel.outlet_id = {outlet_id}
            union  all 
            select rel2.delivery_cycle_id 
            from purchase_request_delivery_cycle_outlet_area_rel as rel2 
            join res_country_area as area on rel2.area_id = area.id
            join stock_warehouse as outlet on outlet.area_id = area.id
            where outlet.id = {outlet_id}""".format(outlet_id=outlet_id)
            self.env.cr.execute(sql)
            res = self.env.cr.fetchall()
            if res:
                dc_ids = [r[0] for r in res]
                args.append(('id', 'in', dc_ids))
            else:
                args.append(('id', 'in', []))
        return super(PurchaseDeliveryCyle, self)._search(
            args=args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid
        )

    @api.onchange('apply_type')
    def oncahnge_apply_type(self):
        if self.apply_type == 'outlet':
            self.area_ids = [(5,)]
        elif self.apply_type == 'area':
            self.outlet_ids = [(5,)]


class PurchaseDeliveryCycleLine(models.Model):
    _name = 'purchase.request.delivery.cycle.line'

    delivery_cycle_id = fields.Many2one(comodel_name='purchase.request.delivery.cycle')
    cutoff_day = fields.Selection(selection=WEEKDAYS, required=True, string=_('Cutoff Day'))
    cutoff_time = fields.Float(related='delivery_cycle_id.cutoff_time', string=_('Cutoff Time'), readonly=True)
    delivery_day = fields.Selection(selection=WEEKDAYS, required=True, string=_('Delivery Day'))
