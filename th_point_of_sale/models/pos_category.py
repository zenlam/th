from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosCategory(models.Model):
    _inherit = "pos.category"

    font_color = fields.Char('Font Color')
    background_color = fields.Char('Background Color')

    _sql_constraints = [('th_pos_categ_name_unique', 'unique(name)',
                         'Category with same name is already exists.')]

    @api.multi
    def unlink(self):
        for categ in self:
            if self.search([('parent_id', '=', categ.id)]):
                raise UserError(
                    _('You cannot delete PoS category (%s),\n'
                      'As it is already used as Parent Category.'
                      % categ.display_name))
        return super(PosCategory, self).unlink()
