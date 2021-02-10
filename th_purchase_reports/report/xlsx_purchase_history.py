from odoo import models
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class XlsxPurchaseHistory(models.AbstractModel):
    _name = 'report.purchase_price_history'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, wb, data, report):
        report_name = 'Purchase Price History'
        ws = wb.add_worksheet(report_name)
        self.set_paper(wb, ws)
        self.styles = self.get_report_styles(wb)
        self.set_header(ws)
        data = self.get_data(report)
        self.bind_data(ws, data, report)

    def set_paper(self, wb, ws):
        wb.formats[0].font_name = 'Times New Roman'
        wb.formats[0].font_size = 12
        ws.set_paper(9)
        ws.set_margins(left=0.28, right=0.28, top=0.5, bottom=0.5)
        ws.fit_to_pages(1, 0)
        ws.set_landscape()
        ws.set_column(0, 6, 25)
        ws.set_column(7, 7, 30)

    def get_report_styles(self, wb):
        styles = {}

        styles['column_header'] = wb.add_format({
            'bold': 1,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12,
            'border': 1,
            'fg_color': '#F5DD13',
        })
        styles['data_left'] = wb.add_format({
            'bold': 0,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12,
            'border': 1,
        })
        styles['data_right'] = wb.add_format({
            'bold': 0,
            'align': 'right',
            'valign': 'vcenter',
            'font_size': 12,
            'border': 1,
        })
        styles['date'] = wb.add_format({
            'bold': 0,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12,
            'num_format': 'dd/mm/yyyy',
            'border': 1,
        })
        styles['num_data'] = wb.add_format({
            'bold': 0,
            'align': 'right',
            'valign': 'vcenter',
            'font_size': 12,
            'num_format': '#,##0.00',
            'border': 1,
        })

        return styles

    def set_header(self, ws):
        row = 0
        col = 0
        ws.write(row, col, 'Product', self.styles['column_header'])
        col += 1
        ws.write(row, col, 'Vendor', self.styles['column_header'])
        col += 1
        ws.write(row, col, 'PO No', self.styles['column_header'])
        col += 1
        ws.write(row, col, 'PO Date', self.styles['column_header'])
        col += 1
        ws.write(row, col, 'Qty Purchased', self.styles['column_header'])
        col += 1
        ws.write(row, col, 'Purchase UOM', self.styles['column_header'])
        col += 1
        ws.write(row, col, 'Unit Price', self.styles['column_header'])
        col += 1
        ws.write(row, col, 'Total Purchased Value',
                 self.styles['column_header'])

    def bind_data(self, ws, data, report):
        row = 1
        col = 0
        for line in data:
            col = 0
            ws.write(row, col, line['product'], self.styles['data_left'])
            col += 1
            ws.write(row, col, line['vendor'], self.styles['data_left'])
            col += 1
            ws.write(row, col, line['po_no'], self.styles['data_left'])
            col += 1
            ws.write(row, col, line['po_date'], self.styles['date'])
            col += 1
            ws.write(row, col, line['qty'], self.styles['data_right'])
            col += 1
            ws.write(row, col, line['uom'], self.styles['data_left'])
            col += 1
            ws.write(row, col, line['unit_price'], self.styles['num_data'])
            col += 1
            ws.write(row, col, line['total_value'], self.styles['num_data'])
            row += 1

    def get_data(self, report):
        condition = self.where(report)
        sql = '''
                SELECT 
                    pt.name as product,
                    rp.name as vendor,
                    po.name as po_no,
                    po.date_order + INTERVAL '8 HOURS' as po_date,
                    sum(pol.product_qty) as qty,
                    uom.name as uom,
                    pol.price_unit as unit_price,
                    sum(pol.product_qty * pol.price_unit) as total_value
                FROM purchase_order_line pol
                    JOIN purchase_order po ON pol.order_id = po.id
                    JOIN product_product pp ON pol.product_id = pp.id
                    JOIN product_template pt ON pp.product_tmpl_id = pt.id
                    JOIN uom_uom uom ON pol.product_uom = uom.id
                    JOIN res_partner rp ON po.partner_id = rp.id
                WHERE 
                    po.state IN ('purchase','done')
                    AND po.date_order BETWEEN '{start_date}' AND '{end_date}'
                    {product_ids}
                    {partner_ids}
                GROUP BY 
                    pt.name,
                    rp.name,
                    po.name,
                    po.date_order,
                    pol.product_qty,
                    uom.name,
                    pol.price_unit
                ORDER BY rp.name
                '''.format(**condition)
        self.env.cr.execute(sql)
        data = self.env.cr.dictfetchall()
        return data

    def where(self, report):
        def _in_condition(obj):
            ids = ['(%s)' % p.id for p in obj]
            ids_string = ", ".join(ids)
            return ids_string

        wheres = {
            'start_date': datetime.combine(report.start_date,
                                           datetime.min.time()) - timedelta(
                hours=8),
            'end_date': datetime.combine(report.end_date,
                                         datetime.max.time()) - timedelta(
                hours=8),
            'product_ids': '',
            'partner_ids': '',
        }

        # Getting product_template_id from wizard and convert to sql where clause
        product_tmpl_ids = report.product_ids or self.env[
            'product.template'].search([])

        products = self.env['product.product'].search(
            [('product_tmpl_id', 'in', product_tmpl_ids.ids)])
        wheres['product_ids'] = _in_condition(products)

        # Getting partner_id from wizard and convert to sql where clause
        partners = report.partner_ids or self.env[
            'res.partner'].search([])
        wheres['partner_ids'] = _in_condition(partners)

        if wheres['product_ids']:
            wheres['product_ids'] = "AND pol.product_id = ANY (VALUES %s)" % \
                                    wheres['product_ids']
        if wheres['partner_ids']:
            wheres['partner_ids'] = "AND po.partner_id = ANY (VALUES %s)" % \
                                    wheres['partner_ids']
        return wheres
