from odoo import models


class OpeningChecklistReport(models.AbstractModel):
    _name = 'report.opening_checklist_wizard'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, wb, data, obj):

        #get wizard value
        all_location = self.env.context.get('all_location', False)
        location_ids = self.env.context.get('location_ids', False)
        report_type = self.env.context.get('report_type', False)
        active_ids = self.env.context.get('active_ids')

        format_header = wb.add_format({
            'bold': 1,
            'align': 'left',
            'font_size': 12,
        })
        format_column_header = wb.add_format({
            'bold': 1,  
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12,
            'border': 1,
        })
        format_column_data = wb.add_format({
            'bold': 0,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12,
            'border': 1,
        })

        for active_id in active_ids:
            row = 0
            col = 0

            checklist_name = self.env['outlet.opening.checklist'].search([(
                'id', '=', active_id
            )])
            report_name = checklist_name.name
            ws = wb.add_worksheet(report_name)
            ws.set_column(0, 14, 25)

            # Excel Report Header & Data
            if all_location:
                if report_type == 'location':
                    for x in checklist_name.checklist_line_ids:
                        ws.write(row, col, 'Opening Checklist (Location)',
                                 format_header)
                        ws.write(row + 1, col, 'Location:', format_header)
                        ws.write(row + 1, col + 1,
                                 x.asset_id.custom_source_department_id.name,
                                 format_header)
                        ws.write(row + 3, col, 'Product', format_column_header)
                        ws.write(row + 3, col + 1, 'Qty on hand',
                                 format_column_header)
                        ws.write(row + 4, col, x.asset_id.name,
                                 format_column_data)
                        ws.write(row + 4, col + 1, x.asset_id.quantity,
                                 format_column_data)

                        row += 8
                else:
                    ws.write(row, col, 'Opening Checklist (Total)',
                             format_header)
                    ws.write(row + 1, col, 'Location:', format_header)
                    ws.write(row + 1, col + 1, ', '.join(
                        set([str(x.asset_id.custom_source_department_id.name)
                             for x in checklist_name.checklist_line_ids])),
                             format_header)
                    ws.write(row + 3, col, 'Product', format_column_header)
                    ws.write(row + 3, col + 1, 'Qty on hand',
                             format_column_header)
                    for x in checklist_name.checklist_line_ids:
                        ws.write(row + 4, col, x.asset_id.name,
                                 format_column_data)
                        ws.write(row + 4, col + 1, x.asset_id.quantity,
                                 format_column_data)
                        row += 1

            else:
                loc = self.env['stock.location'].search([
                    ('id', 'in', location_ids)
                ])
                if report_type == 'location':
                    for location in loc:
                        ws.write(row, col, 'Opening Checklist (Location)',
                                 format_header)
                        ws.write(row + 1, col, 'Location:', format_header)
                        ws.write(row + 1, col + 1, location.name, format_header)
                        ws.write(row + 3, col, 'Product', format_column_header)
                        ws.write(row + 3, col + 1, 'Qty on hand',
                                 format_column_header)
                        for x in checklist_name.checklist_line_ids:
                            if x.asset_id.custom_source_department_id.id == \
                                    location.id:
                                ws.write(row + 4, col, x.asset_id.name,
                                         format_column_data)
                                ws.write(row + 4, col + 1, x.asset_id.quantity,
                                         format_column_data)
                                row += 1
                        row += 8
                else:
                    ws.write(row, col, 'Opening Checklist (Total)',
                             format_header)
                    ws.write(row + 1, col, 'Location:', format_header)
                    ws.write(row + 1, col + 1,
                             ', '.join(set([str(x.name) for x in loc])),
                             format_header)
                    ws.write(row + 3, col, 'Product', format_column_header)
                    ws.write(row + 3, col + 1, 'Qty on hand',
                             format_column_header)
                    for x in checklist_name.checklist_line_ids:
                        ws.write(row + 4, col, x.asset_id.name,
                                 format_column_data)
                        ws.write(row + 4, col + 1, x.asset_id.quantity,
                                 format_column_data)
                        row += 1
