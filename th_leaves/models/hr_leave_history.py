from odoo import api, fields, models, _

class HrLeaveHistory(models.Model):
    _name = "hr.leave.history"

    emp_id = fields.Many2one('hr.employee', string='Employee')
    emp_barcode = fields.Char('Employee ID')
    leave_type = fields.Many2one('hr.leave.type', string='Leave Type')
    apply_date = fields.Date('Apply Date')
    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')
    duration = fields.Float('Durations')
    is_emergency = fields.Boolean('Is Emergency', default=False)
    description = fields.Text('Descriptions')
    approved_by = fields.Many2one('hr.employee', string='Approved By')
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved')
    ], string='Status', default='confirm')
    remaining_leave = fields.Float('Remaining Leaves')

