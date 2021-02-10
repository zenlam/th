from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, Warning


class ThSmartSelectLabel(models.Model):
    _name = 'th.smart.select.label'
    _description = 'TH Smart Select Label'
    _order = 'sequence'

    sequence = fields.Integer(help="Gives the sequence order when displaying "
                                   "a list of labels.")
    name = fields.Char('Name', required=True)

    _sql_constraints = [('th_smart_select_name_unique', 'unique(name)',
                         'Name is already exists.')]

    @api.multi
    def unlink(self):
        for lable in self:
            ss_lines = self.env['th.smart.select.line'].search([
                ('smart_label_id', '=', lable.id)])
            if ss_lines:
                raise Warning(_("Can not delete label(s), "
                                "as it's already used inside Smart Select."))
        return super(ThSmartSelectLabel, self).unlink()


class ThSmartSelectLine(models.Model):
    _name = 'th.smart.select.line'
    _description = 'TH Smart Select Lines'
    _rec_name = 'product_id'
    _order = 'sequence'

    sequence = fields.Integer(help="Gives the sequence order when displaying "
                                   "a list of labels.")
    smart_select_id = fields.Many2one('th.smart.select', 'Smart Selection')
    product_id = fields.Many2one('product.product', 'Menu',
                                 domain=[('is_menu_item', '=', True),
                                         ('is_menu_combo', '=', False)],
                                 required=True)
    smart_label_id = fields.Many2one('th.smart.select.label', 'Label',
                                     required=True)
    show_in_pos = fields.Boolean('Show for Selection in POS')
    font_color = fields.Char('Font Color')
    background_color = fields.Char('Background Color')

    @api.multi
    def unlink(self):
        for line in self:
            line.product_id.product_tmpl_id.write({
                'smart_select_id': False,
            })
        return super(ThSmartSelectLine, self).unlink()


class ThSmartSelect(models.Model):
    _name = 'th.smart.select'
    _description = 'TH Smart Select'

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name', required=True)
    smart_menu_ids = fields.One2many('th.smart.select.line', 'smart_select_id',
                                     'Smart Menus')

    @api.model
    def create(self, values):
        res = super(ThSmartSelect, self).create(values)
        default_menus = []
        if len(res.smart_menu_ids) > 5:
            raise Warning(_('Can not have more than 5 options '
                            'for Smart selection.'))
        for menu in res.smart_menu_ids:
            menu.product_id.product_tmpl_id.write({
                'smart_select_id': res.id,
            })
            if menu.show_in_pos:
                default_menus.append(menu.show_in_pos)

        if not default_menus:
            raise ValidationError(_('There is no menu shown in POS '
                                    'for active smart selection.'))
        if len(default_menus) > 1:
            raise ValidationError(_('You can not set multiple menus '
                                    'to shown in POS for '
                                    'active smart selection.'))
        return res

    @api.multi
    def write(self, values):
        res = super(ThSmartSelect, self).write(values)
        for ss in self:
            default_menus = []
            if len(ss.smart_menu_ids) > 5:
                raise Warning(_('Can not have more than 5 options '
                                'for Smart selection.'))

            for menu in ss.smart_menu_ids:
                menu.product_id.product_tmpl_id.write({
                    'smart_select_id': ss.id,
                })
                if menu.show_in_pos:
                    default_menus.append(menu.show_in_pos)

            if not default_menus:
                raise ValidationError(_('There is no menu shown in POS '
                                        'for active smart selection.'))
            if len(default_menus) > 1:
                raise ValidationError(_('You can not set multiple menus '
                                        'to shown in POS for '
                                        'active smart selection.'))
        return res
