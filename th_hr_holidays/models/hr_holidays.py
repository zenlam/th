from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY


class HrHolidaysItem(models.Model):
    _name = "hr.holidays.item"

    date = fields.Date(string="Date")
    day = fields.Selection([('monday', 'Monday'), ('tuesday', 'Tuesday'), ('wednesday', 'Wednesday'),
                            ('thursday', 'Thursday'), ('friday', 'Friday'), ('saturday', 'Saturday'),
                            ('sunday', 'Sunday')], string="Day", default="monday")
    reason = fields.Char(string="Reason")
    region_id = fields.Many2one(string="Region", comodel_name="res.country.area")
    holiday_id = fields.Many2one(string="Holidays", comodel_name="hr.holidays")

    @api.onchange('date')
    def _onchange_date(self):
        if self.date:
            self.day = self.date.strftime('%A').lower()

    @api.onchange('day')
    def _onchange_day(self):
        if self.date and self.date.strftime('%A').lower() != self.day:
            raise ValidationError('Not Matched!!!')


HrHolidaysItem()


class HrHolidays(models.Model):
    _name = "hr.holidays"

    name = fields.Char(string="Holiday", required=True)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('validated', 'Validated')],
                             string="State", default="draft")
    holidays_item = fields.One2many('hr.holidays.item', 'holiday_id', string='Holidays')
    company_id = fields.Many2one(string="Company", comodel_name="res.company")

    def check_same_duration(self, values):
        start_date = values['start_date'] if 'start_date' in values else self.start_date
        end_date = values['end_date'] if 'end_date' in values else self.end_date
        holidays_item = values['holidays_item']
        if type(start_date) == str:
            start_date = datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT).date()
        if type(end_date) == str:
            end_date = datetime.strptime(end_date, DEFAULT_SERVER_DATE_FORMAT).date()

        def get_date(_date):
            return [item[2]['date'] for item in holidays_item if item[2] and item[2]['date'] == _date]

        for x in holidays_item:
            data = x[2]
            if data and 'date' in data:
                _date = data['date']
                if _date:
                    _date = datetime.strptime(_date, DEFAULT_SERVER_DATE_FORMAT).date()
                if len(self.holidays_item.search([['date', '=', _date], ['holiday_id', '!=', False]])) > 0 or len(get_date(data['date'])) > 1:
                    self.raise_wn_same_duration()
                if _date and (_date < start_date or _date > end_date):
                    raise ValidationError('Date must be in duration')

    def raise_wn_same_duration(self):
        raise ValidationError('Only one active public holiday allowed for same duration. Please change the duration')

    @api.multi
    def action_confirm(self):
        raise_wn = len(self.search([['state', '=', 'confirmed'], ['start_date', '>=', self.start_date],
                                    ['end_date', '<=', self.end_date]])) > 0
        for x in self.holidays_item:
            if len(x.search([['date', '=', x.date], ['id', '!=', x.id], ['holiday_id', '!=', False]])) > 0:
                raise_wn = True
                break
        if raise_wn:
            self.raise_wn_same_duration()
        self.write({'state': 'confirmed'})

    @api.model
    def create(self, values):
        if 'holidays_item' in values:
            self.check_same_duration(values)
        res = super(HrHolidays, self).create(values)
        return res

    def write(self, values):
        if 'holidays_item' in values:
            self.check_same_duration(values)
        res = super(HrHolidays, self).write(values)
        return res

    @api.multi
    def action_validate(self):
        self.write({'state': 'validated'})

    @api.model
    def date_range(self, start_date, end_date):
        for n in range(int((end_date - start_date).days)+1):
            yield start_date + timedelta(n)

    @api.model
    def get_days_match(self, start_date, end_date, employee_id=False):
        data = []
        for single_date in self.date_range(start_date, end_date):
            data.append(single_date.strftime("%Y-%m-%d"))
        domain = [['date', 'in', data]]

        if employee_id:
            employee_id = self.env['hr.employee'].browse(employee_id)
            region_id = employee_id.region_id
            if region_id:
                domain.append(['region_id', 'in', [region_id.id, False]])
        result = self.env['hr.holidays.item'].search(domain)
        days = 0
        for x in result:
            _date_time = datetime.combine(x.date, datetime.min.time())
            start_date = _date_time.replace(hour=0, minute=0, second=0)
            end_date = _date_time.replace(hour=23, minute=59, second=59)
            if employee_id:
                days += employee_id.get_work_days_data(start_date, end_date)['days']
            else:
                days += self.env.user.company_id.resource_calendar_id.get_work_hours_count(start_date, end_date) / \
                        HOURS_PER_DAY
        if self.env.context.get('raise_wn', False) and len(data) == 1 and len(result) == 1:
            raise ValidationError('It is a public holiday, no leave request can be applied on this day')
        return days


HrHolidays()

