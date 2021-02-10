from odoo import api, fields, models, _


class EmergencyConfirmation(models.TransientModel):
    _name = 'emergency.confirmation'
    _description = 'Emergency Leave Confirmation'

    leave_id = fields.Many2one('hr.leave', 'stock_picking_backorder_rel')

    def apply_emergency(self):
        self.leave_id.is_emergency = True
        self.leave_id.action_confirm()

    @api.model
    def default_get(self, fields):
        res = {}
        active_id = self._context.get('active_id')
        if active_id:
            res = {'leave_id': active_id}
        return res