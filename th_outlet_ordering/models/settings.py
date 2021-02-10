# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResCompnay(models.Model):
    _inherit = 'res.company'

    outlet_ordering_cutoff_time_internal = fields.Float()
    outlet_ordering_cutoff_time_1 = fields.Float()
    outlet_ordering_cutoff_time_2 = fields.Float()


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    outlet_ordering_cutoff_time_internal = fields.Float(string=_('Cut-off Time Internal'), readonly=False,
                                                        related='company_id.outlet_ordering_cutoff_time_internal')
    outlet_ordering_cutoff_time_1 = fields.Float(string=_('Ordering Cut-off Time (HAVI)'), readonly=False,
                                                 related='company_id.outlet_ordering_cutoff_time_1')
    outlet_ordering_cutoff_time_2 = fields.Float(string=_('2nd Cut-off Time (HAVI)'), readonly=False,
                                                 related='company_id.outlet_ordering_cutoff_time_2')
