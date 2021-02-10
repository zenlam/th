from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    role_id = fields.Many2one(string="Role", comodel_name="planning.role")
    working_time_rule_id = fields.Many2one(string="Working Time Rules", comodel_name="working.time.rules")

    @api.onchange('working_time_rule_id')
    def onchange_working_time_rule(self):
        if self.working_time_rule_id.company_id != self.company_id:
            raise ValidationError("Company not matched!!!")

    @api.onchange('company_id')
    def _onchange_company(self):
        super(HrEmployee, self)._onchange_company()
        self.onchange_working_time_rule()

    @api.model
    def get_domain_with_outlet(self):
        outlet_id = self.env.context.get('outlet_id', False)
        res = []
        if outlet_id:
            user_ids = self.env['res.users'].search(
                ['|', ('manager_outlet_ids', 'in', [outlet_id]), ('user_outlet_ids', 'in', [outlet_id])])
            res = ('user_id', 'in', [x.id for x in user_ids])
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        _domain = self.get_domain_with_outlet()
        if len(_domain):
            args = args or []
            args.append(_domain)
        res = super(HrEmployee, self).name_search(name=name, args=args, operator=operator, limit=limit)
        return res

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        _domain = self.get_domain_with_outlet()
        if len(_domain):
            domain = domain or []
            domain.append(_domain)
        res = super(HrEmployee, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
        return res


HrEmployee()
