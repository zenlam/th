# __author__ = 'trananhdung'
# -*- coding: utf-8 -*-

from odoo import models, api, fields, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.depends('move_type', 'move_lines.state', 'move_lines.picking_id', 'in_transit')
    @api.one
    def _compute_state(self):
        ''' State of a picking depends on the state of its related stock.move
        - Draft: only used for "planned pickings"
        - Waiting: if the picking is not ready to be sent so if
          - (a) no quantity could be reserved at all or if
          - (b) some quantities could be reserved and the shipping policy is "deliver all at once"
        - Waiting another move: if the picking is waiting for another move
        - Ready: if the picking is ready to be sent so if:
          - (a) all quantities are reserved or if
          - (b) some quantities could be reserved and the shipping policy is "as soon as possible"
        - Done: if the picking is done.
        - Cancelled: if the picking is cancelled
        '''
        if not self.move_lines:
            state = 'draft'
        elif any(move.state == 'draft' for move in self.move_lines):  # TDE FIXME: should be all ?
            state = 'draft'
        elif all(move.state == 'cancel' for move in self.move_lines):
            state = 'cancel'
        elif all(move.state in ['cancel', 'done'] for move in self.move_lines):
            state = 'done'
        else:
            relevant_move_state = self.move_lines._get_relevant_state_among_moves()
            if relevant_move_state == 'partially_available':
                state = 'assigned'
            else:
                state = relevant_move_state
        if state == 'assigned' and self.in_transit:
            state = 'in_transit'
        self.state = state

    outlet_ordering_id = fields.Many2one(comodel_name='outlet.ordering', string=_('Outlet Ordering'))
    in_transit = fields.Boolean(string=_('is In Transit?'), default=False)
    state = fields.Selection([
            ('draft', 'Draft'),
            ('waiting', 'Waiting Another Operation'),
            ('confirmed', 'Waiting'),
            ('in_transit', _('In Transit')),
            ('assigned', 'Ready'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
            ('pending', 'Pending for Approval'),
            ('approve', 'Sender Approved'),
        ], compute='_compute_state', store=True)
