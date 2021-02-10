# __author__ = 'trananhdung'

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError


class ResCountryArea(models.Model):
    _name = "res.country.area"
    _rec_name = 'display_name'

    def get_full_name(self):
        if not self.id:
            return False
        if self.parent_id.id == self.id:
            return
        parent_name = self.parent_id.get_full_name()
        name = (parent_name + '/' + self.name) if parent_name else self.name
        return name

    @api.multi
    def _compute_display_name(self):
        for r in self:
            r.display_name = r.get_full_name()

    display_name = fields.Char(string=_('Display Name'), compute='_compute_display_name')
    name = fields.Char(string="Area Name", required=1)
    code = fields.Char(string="Area Code", required=1)
    parent_id = fields.Many2one(string="Parent Area", comodel_name="res.country.area")
    country_id = fields.Many2one(comodel_name='res.country', string=_('Country'), required=True)

    _sql_constraints = [
        ('code_uniq', 'unique (code)', "Code of Area already exists!\n"
                                       "Please cancel this pop up and change code of the new area creation."),
        ('name_uniq', 'unique (name)', "This Area Name already exists!.\n"
                                       "Please cancel this pop up and rename the new area creation."),
    ]

    @api.multi
    @api.constrains('parent_id')
    def constraint_parent_area(self):
        for r in self:
            if r.parent_id.id == r.id:
                raise ValidationError(_('Cannot set parent is itself'))
    
    @api.multi
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        if default is None:
            default = {}
        if 'name' not in default:
            default['name'] = self[0].name + ' - COPY'
        if 'code' not in default:
            default['code'] = self[0].code + ' - COPY'
        return super(ResCountryArea, self).copy(default)
