from odoo import models
from datetime import datetime, timedelta


class AccountAssetExcel(models.AbstractModel):
    _name = 'report.fixed_asset_register'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, wb, data, obj):
        report_name = 'Assets'
        ws = wb.add_worksheet(report_name)
        ws.set_column(0, 14, 25)
        format_header = wb.add_format({
            'bold': 1,
            'align': 'left',
            'font_size': 12,
        })
        format_header_data = wb.add_format({
            'bold': 0,
            'align': 'left',
            'valign': 'vcenter',
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
        format_create_date = wb.add_format({
            'bold': 0,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12,
            'num_format': 'dd/mm/yyyy hh:mm:ss',
        })
        format_date = wb.add_format({
            'bold': 0,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12,
            'num_format': 'dd/mm/yyyy',
        })
        format_date_data = wb.add_format({
            'bold': 0,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12,
            'num_format': 'dd/mm/yyyy',
            'border': 1,
        })
        # argument for SQL query
        arguments = {
            'start_date': obj.start_date,
            'end_date': obj.end_date
        }
        now = datetime.now() + timedelta(hours=8)
        # Excel Report Header
        row = 0
        col = 0
        ws.write(row, col, 'Name', format_header)
        ws.write(row, col + 1, 'Fixed Asset Register', format_header_data)
        ws.write(row + 1, col, 'Report Print Date', format_header)
        ws.write(row + 1, col + 1, now, format_create_date)
        ws.write(row + 2, col, 'Asset Start Date', format_header)
        ws.write(row + 2, col + 1, obj.start_date, format_date)
        ws.write(row + 3, col, 'Asset End Date', format_header)
        ws.write(row + 3, col + 1, obj.end_date, format_date)

        # Fill in the column name
        row = 6
        col = 0
        ws.write(row, col, 'Serial No.', format_column_header)
        col += 1
        ws.write(row, col, 'Identification No.', format_column_header)
        col += 1
        ws.write(row, col, 'Name of Asset', format_column_header)
        col += 1
        ws.write(row, col, 'Description', format_column_header)
        col += 1
        ws.write(row, col, 'Purchase Date', format_column_header)
        col += 1
        ws.write(row, col, 'Purchase Cost of the Asset', format_column_header)
        col += 1
        ws.write(row, col,
                 'Date when the Asset is put to use', format_column_header)
        col += 1
        ws.write(row, col, 'Depreciation Method', format_column_header)
        col += 1
        ws.write(row, col, 'Depreciation Rate', format_column_header)
        col += 1
        ws.write(row, col, 'Amount of Depreciation', format_column_header)
        col += 1
        ws.write(row, col, 'Gross Book Value', format_column_header)
        col += 1
        ws.write(row, col, 'Net Book Value', format_column_header)
        col += 1
        ws.write(row, col, 'Expected Salvage Value', format_column_header)

        row = 7
        # get the asset data
        assets = self.get_asset_data(arguments)
        # fill in the worksheet
        for asset in assets:
            col = 0
            ws.write(row, col, asset['custom_serial_number'], format_column_data)
            col += 1
            ws.write(row, col, asset['asset_id_number'], format_column_data)
            col += 1
            ws.write(row, col, asset['name'], format_column_data)
            col += 1
            ws.write(row, col, asset['custom_description'], format_column_data)
            col += 1
            ws.write(row, col, asset['purchase_date'], format_date_data)
            col += 1
            ws.write(row, col, asset['value'], format_column_data)
            col += 1
            ws.write(row, col, asset['date'], format_date_data)
            col += 1
            ws.write(row, col, asset['method'], format_column_data)
            col += 1
            ws.write(row, col, asset['d_rate'], format_column_data)
            col += 1
            ws.write(row, col, asset['d_value'], format_column_data)
            col += 1
            ws.write(row, col, asset['d_base'], format_column_data)
            col += 1
            ws.write(row, col, asset['value_residual'], format_column_data)
            col += 1
            ws.write(row, col, asset['salvage_value'], format_column_data)
            row += 1

    def get_asset_data(self, args):
        sql = '''
                SELECT
                custom_serial_number,
                asset_id_number,
                name,
                custom_description,
                purchase_date,
                value,
                date,
                method,
                depreciation_rate AS d_rate,
                depreciated_value AS d_value,
                depreciation_base AS d_base,
                value_residual,
                salvage_value
                FROM account_asset_asset_custom
                WHERE date >= '{start_date}' 
                AND date <= '{end_date}'
                AND state in ('open', 'close')
                ORDER BY ID
                '''.format(**args)
        self.env.cr.execute(sql)
        data = self.env.cr.dictfetchall()
        return data
