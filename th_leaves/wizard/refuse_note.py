from odoo import api, fields, models, _


class RefuseNote(models.TransientModel):
    _name = 'refuse.note'
    _description = 'Refuse Note'
    leave_id = fields.Many2one('hr.leave', 'stock_picking_backorder_rel')
    refuse_note = fields.Text('Refuse Note', required=True)

    def refuse(self):
        self.leave_id.refuse_note = self.refuse_note
        self.leave_id.action_refuse()

    @api.model
    def default_get(self, fields):
        res = {}
        active_id = self._context.get('active_id')
        if active_id:
            res = {'leave_id': active_id}
        return res
