# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import fields, api, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError
from odoo.tools.config import config
import os
import csv
import base64
import pytz
from datetime import timedelta, datetime, date, time

edi_input_path = config.get_misc('edi-integration', 'edi_input_path')
edi_output_path = config.get_misc('edi-integration', 'edi_output_path')
odoo_input_path = config.get_misc('edi-integration', 'odoo_input_path')
odoo_output_path = config.get_misc('edi-integration', 'odoo_output_path')

OUTLET_ORDERING_PATH = 'outlet_ordering'


class OutletOrdering(models.Model):
    _inherit = ['mail.thread']
    _name = 'outlet.ordering'

    @api.model
    def _get_default_outlet(self):
        """
        Get default outlet for ordering for outlet_id
        System will auto fill outlet assigned to current user.
        If user is a regional manager that assigned multiple outlet, this field will be empty
        :return:
        """
        current_user = self.env.user
        outlets = current_user.user_outlet_ids | current_user.manager_outlet_ids
        return outlets.ids[0] if len(outlets.ids) == 1 else False

    @api.multi
    @api.depends('line_ids.price_subtotal')
    def _compute_price_total(self):
        for r in self:
            r.price_total = sum(r.line_ids.mapped('price_subtotal'))

    @api.multi
    @api.depends('picking_ids')
    def _compute_picking_count(self):
        for r in self:
            r.picking_count = len(r.picking_ids.ids)

    name = fields.Char(string=_('Name'), readonly=True, copy=False)
    state = fields.Selection(selection=[('draft', _('Draft')),
                                        ('submit', _('Submit to HAVI')),
                                        ('transit', _('Transit Data Received')),
                                        ('done', _('Done')),
                                        ('cancelled', _('Cancelled'))], readonly=1,
                             string=_('Status'), default='draft', track_visibility='onchange', copy=False)
    requester_id = fields.Many2one(comodel_name='res.users', string=_('Requester'), default=lambda self: self.env.user)
    date_create = fields.Date(string=_('Creation Date'), copy=False,
                              default=lambda self: fields.Date.context_today(self, fields.Datetime.now()))
    outlet_id = fields.Many2one(comodel_name='stock.warehouse', domain=[('create_from', '=', 'outlet')],
                                required=True, default=_get_default_outlet)
    template_id = fields.Many2one(comodel_name='outlet.ordering.template', string=_('Ordering Template'),
                                  required=True)
    delivery_cycle_id = fields.Many2one(comodel_name='outlet.ordering.delivery_cycle',
                                        string=_('Delivery Cycle'), required=True)
    date_creation = fields.Date(string=_('Creation Date'), radonly=True,
                                default=lambda self: fields.Date.context_today(self, fields.Datetime.now()))
    date_delivery_request = fields.Date(string=_('Request Delivery Date'), required=False)
    date_submission = fields.Datetime(string=_('Submission Date'), copy=False)
    special = fields.Boolean(string=_('Special Order'), default=False, readonly=True, copy=False)
    stock_coverage_day = fields.Integer(string=_('Stock Coverage Day'))

    cutoff_1 = fields.Datetime(string=_('1st Cut-off Time (MM:HH)'), required=False, copy=False)
    cutoff_2 = fields.Datetime(string=_('2nd Cut-off Time (MM:HH)'), required=False, copy=False)

    delay_vendor = fields.Integer(string=_('Lead Time (days)'))

    # Address
    street = fields.Char(related='outlet_id.street', readonly=True)
    street2 = fields.Char(related='outlet_id.street2', readonly=True)
    zip = fields.Char(related='outlet_id.zip', change_default=True, readonly=True)
    city = fields.Char(related='outlet_id.city', readonly=True)
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               related='outlet_id.state_id', readonly=True)
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict',
                                 related='outlet_id.country_id', readonly=True)
    outlet_shipping_address = fields.Char(string=_('Outlet Receiving Address'),
                                          related='outlet_id.address', readonly=True)

    user_cancelled_id = fields.Many2one(comodel_name='res.users', string=_('Cancelled by'), copy=False)
    user_rejected_id = fields.Many2one(comodel_name='res.users', string=_('Rejected by'), copy=False)
    user_approved_id = fields.Many2one(comodel_name='res.users', string=_('Approved by'), copy=False)
    csv_data = fields.Binary(string=_('CSV Data'), readonly=True, copy=False)
    csv_filename = fields.Char(string=_('CSV File'), copy=False)
    remark = fields.Text(string=_('Remark'))
    price_total = fields.Float(string=_('Total'), compute='_compute_price_total')

    line_ids = fields.One2many(comodel_name='outlet.ordering.line', inverse_name='order_id')
    picking_ids = fields.One2many(comodel_name='stock.picking', string=_('Receipts'), inverse_name='outlet_ordering_id')
    picking_count = fields.Integer(string=_('Picking Count'), compute='_compute_picking_count', store=True)
    generated_csv = fields.Boolean(string=_('CSV is Generated?'), default=False)
    # @api.onchange('date_delivery_request', 'delivery_cycle_id')
    # def onchange_delivery_cycle_date_delivery_request(self):
    #     if self.date_delivery_request and self.delivery_cycle_id.id:
    #         for line in self.delivery_cycle_id

    @api.onchange('outlet_id')
    def onchange_outlet(self):
        if self.outlet_id.id:
            delivery_cycle = self.env['outlet.ordering.delivery_cycle'].search(
                ['|', '&', ('apply_type', '=', 'outlet'), ('outlet_id', '=', self.outlet_id.id),
                 '&', ('apply_type', '=', 'area'), ('area_id', '=', self.outlet_id.area_id.id)]
            )
            if len(delivery_cycle.ids) == 1:
                self.delivery_cycle_id = delivery_cycle
            else:
                self.delivery_cycle_id = False
            return {'domain': {'delivery_cycle_id': [('id', 'in', delivery_cycle.ids)]}}

    def _generate_csv_data(self):
        """
        TODO: Prepare data follow havi format
        :return:
        """
        filename = 'THM_{name}_{date}.csv'.format(name=self.name, date=fields.Datetime.now().strftime('%Y%m%d%H%M%S'))

        # this one for testing, will remove later
        data = []
        base_line = [self.name,
                     self.outlet_id.id,
                     fields.Datetime.to_date(self.date_submission).strftime('%Y%m%d'),
                     fields.Date.to_date(self.date_delivery_request).strftime('%Y%m%d')]
        for line in self.line_ids:
            data_line = base_line + [line.product_id.default_code,
                                     line.product_id.default_code,
                                     line.qty_order,
                                     line.product_id.barcode]
            data.append(data_line)

        pull_path = os.path.join(odoo_output_path, OUTLET_ORDERING_PATH, filename)
        with open(pull_path, 'w') as f:
            wr = csv.writer(f, quoting=csv.QUOTE_ALL)
            for row in data:
                wr.writerow(row)

        data = base64.b64encode(open(pull_path, 'rb').read())
        return data, filename

    def send_data(self):
        """

        :return:
        """
        csv, filename = self._generate_csv_data()
        self.write({'csv_data': csv,
                    'csv_filename': filename})
        self.env['th.edi.api'].send_csv(csv_path=os.path.join(odoo_output_path, OUTLET_ORDERING_PATH, filename),
                                        dest_path=OUTLET_ORDERING_PATH)  # See on th_edi_api/edi.py
        return

    @api.multi
    def action_submit(self):
        """
        TODO: submit flow
        :return:
        """
        self.ensure_one()
        name = self.name or self.env.ref('th_outlet_ordering.th_outlet_ordering_name_sequence').next_by_id()
        submission_time = fields.Datetime.now()
        submission_date = submission_time.date()
        submission_date_weekday = submission_date.weekday()
        delivery_days = self.delivery_cycle_id.line_ids.mapped('delivery_day')
        delivery_days.sort()
        if len(delivery_days) == 0:
            raise ValidationError(_("Delivery Cycle don't have any configuration for delivery day!"))
        delivery_day = int(delivery_days[0])
        for dy in delivery_days:
            if submission_date_weekday < int(dy):
                delivery_day = int(dy)
                break

        date_delta = delivery_day - submission_date_weekday
        date_delta = date_delta if date_delta >= 0 else date_delta + 7
        delivery_date = (submission_date + timedelta(days=date_delta))
        cycle_line = self.delivery_cycle_id.line_ids.filtered(lambda x: int(x.delivery_day) == delivery_day)

        cutoff_date_delta = int(cycle_line.cutoff_day) - int(cycle_line.delivery_day)
        cutoff_date_delta = cutoff_date_delta if cutoff_date_delta <= 0 else cutoff_date_delta - 7
        cutoff_date = delivery_date + timedelta(days=cutoff_date_delta)
        cutoff_1 = datetime.combine(cutoff_date, time(hour=int(cycle_line.cutoff_time_1),
                                                      minute=int((cycle_line.cutoff_time_1 - int(cycle_line.cutoff_time_1)) * 60)))
        cutoff_2 = datetime.combine(cutoff_date, time(hour=int(cycle_line.cutoff_time_2),
                                                      minute=int((cycle_line.cutoff_time_2 - int(cycle_line.cutoff_time_2)) * 60)))
        tz = self.env.context.get('tz', False) or 'Asia/Kuala_Lumpur'
        tz = datetime.now(pytz.timezone(tz))
        cutoff_1 -= tz.tzinfo._utcoffset
        cutoff_2 -= tz.tzinfo._utcoffset
        if submission_time > cutoff_2:
            raise ValidationError(_('You cannot submit this Order because the time limit has been exceeded'))
        if submission_time > cutoff_1:
            special = True
        else:
            special = False
        self._generate_order_picking()
        self.write({'state': 'submit',
                    'date_submission': submission_time,
                    'date_delivery_request': delivery_date,
                    'user_approved_id': self.env.user.id,
                    'cutoff_1': cutoff_1,
                    'cutoff_2': cutoff_2,
                    'special': special,
                    'name': name,
                    })

        # self.send_data()

        return True

    @api.multi
    def action_transit_data(self):
        """
        Deprecated function. It will be removed later.
        Now, this function use to test work flow
        :return:
        """
        self.write({'state': 'transit'})
        return True

    @api.multi
    def action_done(self):
        """

        :return:
        """
        self.write({'state': 'done'})
        return True

    @api.multi
    def action_cancel(self):
        """

        :return:
        """
        self.write({'state': 'cancelled', 'user_cancelled_id': self.env.user.id})

    @api.multi
    def action_set_to_draft(self):
        """
        Reset Order to Draft for testing. I don't want to create many order
        so I need to cancel it then set to draft to start the work flow again
        :return:
        """
        self.write({'state': 'draft'})

    @api.multi
    def button_calculate_qty(self):
        """
        Use to manually get suggestion quantity on order lines
        :return:
        """
        self.ensure_one()
        for line in self.line_ids:
            line._calculate_suggestion_qty()

    def _prepare_picking_vals(self):
        vals = {
            'location_id': self.env.ref('th_outlet_ordering.th_havi_location').id,
            'location_dest_id': self.outlet_id.lot_stock_id.id,
            'picking_type_id': self.env.ref('th_outlet_ordering.th_havi_ordering_picking_type').id,
            'origin': self.name,
            'outlet_ordering_id': self.id,
        }
        return vals

    def _prepare_move_vals(self, line, picking):
        vals = {
            'name': '/',
            'product_id': line.product_id.id,
            'product_uom_qty': line.qty_order,
            'product_uom': line.uom_order.id,
            'picking_id': picking.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'account_analytic_id': self.outlet_id.analytic_account_id.id
        }
        return vals

    def _generate_order_picking(self):
        picking_vals = self._prepare_picking_vals()
        picking = self.env['stock.picking'].create(picking_vals)
        for order_line in self.line_ids:
            move_vals = self._prepare_move_vals(order_line, picking)
            self.env['stock.move'].create(move_vals)

        return picking

    def _fill_picking_from_havi_csv_data(self, csv_data):
        """
        TODO: generate picking follow csv data
        :return:
        :param csv_data: csv format - delivery notes info
        :return:
        """

        pass

    @api.multi
    def receive_delivery_note_from_edi(self, csv_data):
        """
        This function will call by EDI via API
        :param csv_data: csv format - delivery notes info
        :return:
        """
        self._fill_picking_from_havi_csv_data(csv_data)
        return self.write({'state': 'transit'})

    @api.multi
    def open_order_picking(self):
        return {
            'name': _('HAVI Internal Transfer'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.picking_ids.ids)],
            'target': 'current',
            'views': [(False, 'tree'),
                      (self.env.ref('th_outlet_ordering.view_picking_form_inherit_havi_extend').id, 'form')]
        }

    @api.multi
    def _generate_csv(self):
        """
        :return:
        """
        filename = 'THM_{date}.csv'.format(date=fields.Datetime.now().strftime('%Y%m%d%H%M%S'))

        # this one for testing, will remove later
        data = []
        for r in self:
            base_line = [r.name,
                         r.outlet_id.id,
                         fields.Datetime.to_datetime(r.date_submission).strftime('%Y%m%d'),
                         fields.Date.to_date(r.date_delivery_request).strftime('%Y%m%d')]
            for line in r.line_ids:
                data_line = base_line + [line.product_id.default_code,
                                         line.product_id.default_code,
                                         line.qty_order,
                                         line.product_id.barcode]
                data.append(data_line)

        pull_path = os.path.join(odoo_output_path, OUTLET_ORDERING_PATH, filename)
        with open(pull_path, 'w') as f:
            wr = csv.writer(f, quoting=csv.QUOTE_ALL)
            for row in data:
                wr.writerow(row)

        self.write({'csv_data': base64.b64encode(open(pull_path, 'rb').read()),
                    'csv_filename': filename,
                    'generated_csv': True})

        return pull_path

    @api.model
    def cron_generate_csv(self, testing=False):
        """

        :return:
        """
        current_time = fields.Datetime.now()
        domain = [('state', '=', 'submit')]
        if not testing:
            domain.extend([('generated_csv', '=', False), ('cutoff_2', '<', current_time)])
        orders = self.search(domain)
        orders_by_outlet = {}
        for order in orders:
            outlet_id = order.outlet_id.id
            if outlet_id not in orders_by_outlet:
                orders_by_outlet[outlet_id] = order
            else:
                orders_by_outlet[outlet_id] |= order

        for outlet_id in orders_by_outlet:
            orders = orders_by_outlet[outlet_id]
            csv_file = orders._generate_csv()
            ref = ', '.join([o.name for o in orders])
            self.env['th.edi.api'].with_context(ref=ref).send_csv(csv_path=csv_file, dest_path=OUTLET_ORDERING_PATH)  # See on th_edi_api/edi.py

    @api.multi
    def test_generate_csv(self):
        """

        :return:
        """
        return self.env[self._name].cron_generate_csv(testing=True)


class OutletOrderingLine(models.Model):
    _name = 'outlet.ordering.line'

    @api.multi
    @api.depends('price_unit', 'qty_order')
    def _compute_price_subtotal(self):
        for r in self:
            r.price_subtotal = r.qty_order * r.price_unit

    order_id = fields.Many2one(comodel_name='outlet.ordering', string=_('Order'))
    product_id = fields.Many2one(comodel_name='product.product', string=_('Product'), required=True)
    qty_onhand = fields.Float(string=_('OnHand Qty'), digits=dp.get_precision('Product Unit of Measure'))
    uom_onhand = fields.Many2one(comodel_name='uom.uom', string=_('OnHand UOM'))
    qty_suggested = fields.Float(string=_('Suggested Qty'), digits=dp.get_precision('Product Unit of Measure'))
    uom_suggested = fields.Many2one(comodel_name='uom.uom', string=_('Suggested UOM'))
    change_type = fields.Selection(selection=[('increase', _('Increase')),
                                              ('same', _('Same')),
                                              ('reduce', _('Reduce'))],
                                   string=_('Increase/Reduce'))
    change_percent = fields.Float(string='%', digits=dp.get_precision('Product Unit of Measure'))
    qty_order = fields.Float(string=_('Order Qty'), digits=dp.get_precision('Product Unit of Measure'))
    uom_order = fields.Many2one(comodel_name='uom.uom', string=_('Order UOM'))
    qty_delivery = fields.Float(string=_('Delivery Qty'), digits=dp.get_precision('Product Unit of Measure'))
    uom_delivery = fields.Many2one(comodel_name='uom.uom', string=_('Delivery UOM'))
    uom_price = fields.Many2one(comodel_name='uom.uom', string=_('U/Price UOM'))
    price_unit = fields.Float(string=_('U/Price'), digits=dp.get_precision('Product Unit of Measure'))
    ration = fields.Float(string=_('Ratio'), digits=dp.get_precision('Product Unit of Measure'))
    price_subtotal = fields.Float(string=_('Total Order Price'), compute='_compute_price_subtotal', store=True)

    def _calculate_suggestion_qty(self):
        """
        TODO: Calculate suggestion quantity
        :return:
        """
        pass
