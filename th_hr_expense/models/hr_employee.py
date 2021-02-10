from odoo import models, fields, api, _


class Employee(models.Model):
    _inherit = "hr.employee"

    @api.model
    def _get_manager_id_domain(self):
        """
        Domain for parent_id and head_of_manager_id
        Show only employees from 3 below groups
         - Manager/Finance of Expenses
         - Manager of Leaves
         - Manager of Employees
        """
        group_ids = []
        user_ids = []
        group_ids.append(self.env.ref('hr_expense.group_hr_expense_user').id)
        group_ids.append(self.env.ref(
            'hr_holidays.group_hr_holidays_manager').id)
        group_ids.append(self.env.ref('hr.group_hr_manager').id)
        for group_id in group_ids:
            users = self.env['res.groups'].search([
                ('id', '=', group_id)
            ]).users
            for user in users:
                user_ids.append(user.id)
        user_ids = list(set(user_ids))
        user_ids.sort()
        res = [('user_id.id', 'in', user_ids)]
        return res

    parent_id = fields.Many2one(
        domain=lambda self: self._get_manager_id_domain())
    head_of_manager_id = fields.Many2one(
        'hr.employee', string="Head of Manager",
        domain=lambda self: self._get_manager_id_domain()
    )
