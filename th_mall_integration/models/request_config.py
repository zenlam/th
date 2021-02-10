from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime, timedelta
from .api_caller import ApiCaller
import ast


REQUEST_METHODS = [
    ('post', 'POST'),
    ('get', 'GET'),
    ('put', 'PUT'),
    ('delete', 'DELETE'),
]


def str2tuple(s):
    return eval('tuple(%s)' % (s or ''))


class ThRequestConfig(models.Model):
    _name = 'th.request.config'
    _description = 'TH Mall Integration Request Configuration'
    _order = 'name'

    name = fields.Char(string="Name")
    is_async = fields.Boolean(string="Asynchronous", default=False)
    active = fields.Boolean(string="Active", default=True)
    request_ids = fields.One2many('th.request.details', inverse_name='config_id')
    outlet_id = fields.Many2one('stock.warehouse', string="Outlet", required=1)
    period = fields.Selection([('daily', 'Daily'), ('monthly', 'Monthly')],
                              required=True, default='daily')

    @api.multi
    def send_requests_manual(self, *args, **kwargs):
        self.ensure_one()
        view = self.env.ref(
            'th_mall_integration.run_request_config_view_form').id
        return {
            'name': _('Run Config'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'th.run.request.config',
            'views': [(view, 'form')],
            'view_id': view,
            'target': 'new',
            'context': {'active_id': self.id},
        }

    @api.multi
    def send_requests(self, *args, **kwargs):
        for conf in self:
            ApiCaller(conf).run(*args, **kwargs)

    def get_logger(self):
        self.ensure_one()
        return self.env['th.request.log'].create({
            'config_id': self.id,
            'name': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        })


class ThRequestDetails(models.Model):
    _name = 'th.request.details'
    _description = 'TH Mall Integration Request Details'
    _order = 'sequence ASC, name ASC'

    name = fields.Char(string="Name")
    url = fields.Char(string="URL")
    request_method = fields.Selection(selection=REQUEST_METHODS,
                                      default='post', string="Request Method")
    sequence = fields.Integer(string="Sequence")
    timeout = fields.Integer(string="Timeout(s)", default=60)
    func_name = fields.Char(string="Method")
    func_args = fields.Char(string="Arguments", default='')
    config_id = fields.Many2one('th.request.config')
    use_fixed_data = fields.Boolean(string="Use Fixed Data", default=True)
    header_id = fields.One2many('th.request.header', inverse_name='request_id',
                                string="Header Information")
    fixed_request_body = fields.Text(string="Request Body", default="[]")

    @api.model
    def mall_integration_request_body(self, date=False):
        if date:
            start_date = None
            # 5:01 is cutoff time for BR (to be confirmed with TH)
            end_date = datetime.strptime(str(date) + ' 05:01:00',
                                         DEFAULT_SERVER_DATETIME_FORMAT)
            date = end_date
        else:
            start_date, end_date = self.get_date_range()

        report = self.env['th.gto.summary.report'].create({
            'date': end_date,
            'from_date': start_date,
            'outlet_id': self.config_id.outlet_id.id
        })
        data, cash = report.get_onsite_offsite_data(), report.get_cash_data()[
            0]['cash'] or 0
        return self.get_payload(data, date)

    def get_date_range(self):
        now = datetime.now() + timedelta(hours=8)
        if self.config_id.period == 'monthly':
            end_date = now.replace(day=1) - timedelta(days=1)
            start_date = now.replace(month=now.month - 1, day=1) - timedelta(
                days=1)
        elif self.config_id.period == 'daily':
            end_date = now - timedelta(days=1)
            start_date = None
        else:
            raise UserWarning(_("Config's period is missing !"))
        return start_date, end_date

    def get_payload(self, data, date):
        if date:
            # do not need to minus 1 day if the date is provided
            # because it is a manual sending
            day_before = date
        else:
            now = datetime.now() + timedelta(hours=8)
            day_before = now - timedelta(days=1)
        # sub_total = data['total'] - data['tax'] + data['discount_before_tax']
        return [{
            "ReceiptNo": day_before.strftime('%Y%m%d'),
            "ReceiptDateAndTime2": day_before.strftime('%Y-%m-%d 00:00:00'),
            # "SubTotal": data['on_site_without_tax'],  # sub_total,
            "DiscountPercent": 0.0,
            # round(float(data['discount']) / sub_total, 2) * 100 if sub_total else 0.0,
            "DiscountAmount": 0.0,  # data['discount_before_tax'],
            "GstPercent": 6.0,
            # "GstAmount": data['on_site_tax'],
            "ServiceChargePercent": 0.0,
            "ServiceChargeAmount": 0.0,
            # "GrandTotal": data['on_site_with_tax'],
            "IsTest": True,
            "IsVoid": False
        }]

    @api.one
    @api.constrains('func_args')
    def _check_args(self):
        """Make sure that arguments is placed in tuple"""
        try:
            str2tuple(self.func_args)
        except SyntaxError:
            return False
        return True

    def normalize_body_data(self, str):
        """
        input data from string may not eval-able
        @param str: string
        @return:
        """
        return str.replace('\n', '').replace('true', 'True').replace('false',
                                                                     'False')

    def get_request_body(self, *args, **kwargs):
        """

        @return: list - request's body
        """
        self.ensure_one()
        request_body = ''
        if self.use_fixed_data:
            request_body = ast.literal_eval(self.normalize_body_data(
                self.fixed_request_body)) if self.fixed_request_body else ''
        else:
            # Get dynamic params
            func = self._params_func()
            if func:
                if not args:
                    args = tuple(self.func_args or '')
                request_body = func(*args, **kwargs)
        return request_body

    def get_request_headers(self):
        """

        @return: dict - request's header
        """
        self.ensure_one()
        headers = {}
        for h in self.header_id:
            headers[h.name] = h.value
        return headers

    def _params_func(self):
        """

        @return: function - function that will be used to get dynamic params
        """
        func = getattr(self, self.func_name)
        return func


class ThRequestHeader(models.Model):
    _name = 'th.request.header'
    _description = 'TH Mall Integration Request Header'

    name = fields.Char(string="Name", required=True)
    value = fields.Char(string="Value")
    request_id = fields.Many2one('th.request.details')
