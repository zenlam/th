# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare

class WizardPoLineDelete(models.TransientModel):
    _name = 'wizard.po.line.delete'

    po_line_id = fields.Many2one('purchase.order.line', required=False)
    po_id = fields.Many2one('purchase.order', required=True)
    product_id = fields.Many2one('product.product', required=True)

    @api.model
    def default_get(self, fields):
        res = super(WizardPoLineDelete, self).default_get(fields)
        active_id = self.env.context.get('active_id', False)
        product_id = False
        po_id = False

        if active_id:
            line = self.env['purchase.order.line'].browse(active_id)
            product_id = line.product_id.id
            po_id = line.order_id.id
        res.update({
            'po_line_id' : active_id,
            'product_id' : product_id,
            'po_id' : po_id
        })
        return res

    @api.multi
    def delete_all_related_po_line(self):
        for pr in self.po_id.purchase_request_ids:
            for pr_line in pr.purchase_request_line_ids:
                if pr_line.product_id.id == self.product_id.id:
                    pr_line.unlink()
        self.po_line_id.unlink()
        return True

