# __author__ = 'trananhdung'

from odoo import models, fields, api
from odoo.tools.translate import _


class ResUsers(models.Model):
    _inherit = 'res.users'

    user_outlet_ids = fields.Many2many(comodel_name='stock.warehouse',
                                      relation='store_user_rel',
                                      string=_('User Outlets'))
    manager_outlet_ids = fields.Many2many(comodel_name='stock.warehouse',
                                         relation='store_manager_user_rel',
                                         string=_('Manager Outlets'))
    other_outlet_ids = fields.Many2many(comodel_name='stock.warehouse',
                                       relation='other_store_user_rel',
                                       string=_('Other Outlets'),
                                       help=_('Config access rights store for other '
                                              'group (not pos.user and pos.manager)'))
    see_all = fields.Boolean(string=_('See All Outlets'), default=False)
