from odoo import models, fields, api, _
from odoo.exceptions import UserError


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    report_type = fields.Selection(selection_add=[("txt", "TXT")])

    @api.model
    def render_txt(self, docids, data):
        if not self and self.env.context.get('report_name'):
            report_model_name = 'report.{}'.format(
                self.env.context['report_name'])
            report_model = self.env.get(report_model_name)
            if report_model is None:
                raise UserError(
                    _('%s model was not found' % report_model_name))
            return report_model.create_txt_report(docids, data)

    @api.model
    def _get_report_from_name(self, report_name):
        res = super(IrActionsReport, self)._get_report_from_name(report_name)
        if res:
            return res
        report_obj = self.env["ir.actions.report"]
        qwebtypes = ["qweb-text"]
        conditions = [
            ("report_type", "in", qwebtypes),
            ("report_name", "=", report_name),
        ]
        context = self.env["res.users"].context_get()
        return report_obj.with_context(context).search(conditions, limit=1)
