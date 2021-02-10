from datetime import datetime
from odoo import models, _
from odoo.exceptions import UserError


class GtoSummaryTxt(models.AbstractModel):
    _name = 'report.gto_summary_report'
    _inherit = 'report.report_txt.abstract'

    def generate_txt_report(self, file, objs):
        template_id = self.env['th.file.transfer.config'].search([
            ('outlet_id', '=', objs.outlet_id.id),
            ('period', '=', 'daily')
        ], limit=1)
        if not template_id:
            raise UserError(_('Your Outlet does not has GTO template. '
                              'Go to Point Of Sale -> Configuration -> Mall '
                              'Integration Config to create Template\n'))
        template = template_id.position
        txt_format = self.get_text_report_format(objs)
        # on_off_data = objs.get_onsite_offsite_data()
        # if on_off_data['on_site_with_tax'] is not None or on_off_data[
        #     'off_site_with_tax'] is not None:
        #     format.update({
        #         'total': '%%0%s.2f' % (template_id.padding + 3) % on_off_data[
        #             'on_site_with_tax'],
        #         'total_on_off': '%%0%s.2f' % (template_id.padding + 3) % (
        #                 on_off_data['on_site_with_tax'] + on_off_data[
        #             'off_site_with_tax']),
        #         'before_tax': '%%0%s.2f' % (
        #                     template_id.before_gst_padding + 3) % on_off_data[
        #                           'on_site_without_tax'],
        #         'before_tax_on_off': '%%0%s.2f' % (
        #                     template_id.before_gst_padding + 3) % (
        #                                      on_off_data[
        #                                          'on_site_without_tax'] +
        #                                      on_off_data[
        #                                          'off_site_without_tax']),
        #         'gst': '%%0%s.2f' % (template_id.gst_padding + 3) %
        #                on_off_data['on_site_tax'],
        #         'gst_on_off': '%%0%s.2f' % (template_id.gst_padding + 3) % (
        #                 on_off_data['on_site_tax'] + on_off_data[
        #             'off_site_tax']),
        #         'discount': '%%0%s.2f' % (
        #                     template_id.discount_padding + 3) % 0,
        #         'ticket_count': '%%0%sd' % (
        #                     template_id.ticket_count_padding + 3) %
        #                         on_off_data['onsite_tc'],
        #         'ticket_off_site': '%%0%sd' % (
        #                     template_id.ticket_count_padding + 3) %
        #                            on_off_data['offsite_tc'],
        #         'ticket_on_off': '%%0%sd' % (
        #                     template_id.ticket_count_padding + 3) % (
        #                          on_off_data['total_tc']),
        #         'other': '%%0%s.2f' % (template_id.other_padding + 3) % (
        #                     on_off_data['on_site_with_tax'] - cash),
        #         'other_on_off': '%%0%s.2f' % (
        #                     template_id.other_padding + 3) % (
        #                                 on_off_data['on_site_with_tax'] +
        #                                 on_off_data[
        #                                     'off_site_with_tax'] - cash),
        #         'other_wo_tax': '%%0%s.2f' % (
        #                     template_id.other_padding + 3) % (
        #                                 on_off_data['on_site_without_tax'] -
        #                                 on_off_data['cash_wo_tax']),
        #         'other_wo_tax_on_off': '%%0%s.2f' % (
        #                     template_id.other_padding + 3) % (
        #                                        on_off_data[
        #                                            'on_site_without_tax'] +
        #                                        on_off_data[
        #                                            'off_site_without_tax'] -
        #                                        on_off_data['cash_wo_tax']),
        #         'cash_wo_tax': '%%0%s.2f' % (template_id.cash_padding + 3) % (
        #                     on_off_data['cash_wo_tax'] or 0)
        #     })
        output = template.format(**txt_format)
        file.write(output)

    def get_text_report_format(self, objs):
        template_id = self.env['th.file.transfer.config'].search([
            ('outlet_id', '=', objs.outlet_id.id),
            ('period', '=', 'daily')
        ], limit=1)
        cash = objs.get_cash_data()[0]['cash']
        date_string = datetime.strftime(objs.date, '%Y-%m-%d')
        date_client = datetime.strptime(date_string, '%Y-%m-%d')
        return {
            'prefix': template_id.prefix,
            'machine': template_id.machine,
            'date': datetime.strftime(
                date_client,
                template_id.date_format or '%Y%m%d'
            ),
            'total': 0,
            'before_tax': 0,
            'cash': '%%0%s.2f' % (template_id.cash_padding + 3) % (
                        cash or 0),
            'other': 0,
            'discount': 0,
            'gst': 0,
            'ticket_count': 0,
            'ticket_off_site': 0,
            'ticket_on_off': 0,
            'sequence': '%%0%sd' %
                        template_id.sequence_padding % template_id.sequence,
            'filename_date': datetime.strftime(
                date_client,
                template_id.filename_date_format or '%Y%m%d'
            ),

        }
