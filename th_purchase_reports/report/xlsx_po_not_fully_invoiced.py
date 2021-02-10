from odoo import models
from datetime import datetime, timedelta


class XlsxPONotFullyInvoiced(models.AbstractModel):
    _name = 'report.po_not_fully_invoiced'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, wb, data, report):
        report_name = 'PO Not Fully Invoiced'
        ws = wb.add_worksheet(report_name)
        self.set_paper(wb, ws)
        self.styles = self.get_report_styles(wb)
        self.set_header(ws, report)
        data = self.get_data(report)
        self.bind_data(ws, data, report)

    def set_paper(self, wb, ws):
        wb.formats[0].font_name = 'Times New Roman'
        wb.formats[0].font_size = 12
        ws.set_paper(9)
        ws.set_margins(left=0.28, right=0.28, top=0.5, bottom=0.5)
        ws.fit_to_pages(1, 0)
        ws.set_landscape()
        ws.set_column(0, 10, 25)

    def get_report_styles(self, wb):
        styles = {}

        styles['header'] = wb.add_format({
            'bold': 1,
            'align': 'left',
            'valign': 'vcenter',
            'font_size': 12,
            'border': 1,
        })
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

    def set_header(self, ws, report):
        type = {'detail': 'Detailed', 'summary': 'Summary',
                'partial': 'Partially Invoiced', 'not': 'Not Invoiced'}
        row = 0
        col = 0
        ws.write(row, col, 'Report Type', self.styles['header'])
        col += 1
        ws.write(row, col, type[report.report_type], self.styles['data_left'])
        row += 1
        col = 0
        ws.write(row, col, 'Invoice Type', self.styles['header'])
        col += 1
        ws.write(row, col, type[report.invoice_type], self.styles['data_left'])

        row = 3
        col = 0
        ws.write(row, col, 'Supplier', self.styles['column_header'])
        col += 1
        ws.write(row, col, 'Product', self.styles['column_header'])
        col += 1
        ws.write(row, col, 'Product Category', self.styles['column_header'])
        col += 1
        ws.write(row, col, 'Product Type', self.styles['column_header'])
        if report.report_type == 'detail':
            col += 1
            ws.write(row, col, 'PO Number', self.styles['column_header'])
        col += 1
        ws.write(row, col, 'PO Quantity', self.styles['column_header'])
        col += 1
        ws.write(row, col, 'Purchase UOM', self.styles['column_header'])
        if report.report_type == 'detail':
            col += 1
            ws.write(row, col, 'Invoice Number', self.styles['column_header'])
            col += 1
            ws.write(row, col, 'Vendor Bill Reference',
                     self.styles['column_header'])
        col += 1
        ws.write(row, col, 'Invoice Qty', self.styles['column_header'])
        col += 1
        ws.write(row, col, 'Invoice UOM', self.styles['column_header'])

    def bind_data(self, ws, data, report):
        product_type = {'product': 'Stockable',
                        'consu': 'Consumable',
                        'service': 'Service'}
        row = 4
        col = 0
        for line in data:
            col = 0
            ws.write(row, col, line['supplier'], self.styles['data_left'])
            col += 1
            ws.write(row, col, line['product'], self.styles['data_left'])
            col += 1
            ws.write(row, col, line['categ'], self.styles['data_left'])
            col += 1
            ws.write(row, col, product_type[line['type']],
                     self.styles['data_left'])
            if report.report_type == 'detail':
                col += 1
                ws.write(row, col, line['po_num'], self.styles['data_right'])
            col += 1
            ws.write(row, col, line['po_qty'], self.styles['data_right'])
            col += 1
            ws.write(row, col, line['po_uom'], self.styles['data_left'])
            if report.report_type == 'detail':
                col += 1
                ws.write(row, col, line['inv_no'], self.styles['data_left'])
                col += 1
                ws.write(row, col, line['bill_ref'], self.styles['data_left'])
            col += 1
            ws.write(row, col, line['inv_qty'], self.styles['data_right'])
            col += 1
            ws.write(row, col, line['inv_uom'], self.styles['data_left'])
            row += 1

    def get_data(self, report):
        statements = {
            'select': self.select(report),
            'where': self.where(report),
            'group_by': self.group_by(report),
        }

        sql = '''
                {select}
                FROM account_invoice_line ail
                    JOIN account_invoice ai ON ail.invoice_id = ai.id
                    JOIN uom_uom uom ON ail.uom_id = uom.id
                    RIGHT JOIN purchase_order_line pol ON ail.purchase_line_id = pol.id
                    JOIN purchase_order po ON pol.order_id = po.id
                    JOIN product_product pp ON ail.product_id = pp.id OR pol.product_id = pp.id
                    JOIN product_template pt ON pp.product_tmpl_id = pt.id
                    JOIN product_category pc ON pt.categ_id = pc.id
                    JOIN res_partner rp ON ai.partner_id = rp.id OR po.partner_id = rp.id
                    JOIN uom_uom uom2 ON pol.product_uom = uom2.id
                {where}
                {group_by}
                ORDER BY rp.name
                '''.format(**statements)
        self.env.cr.execute(sql)
        data = self.env.cr.dictfetchall()
        return data

    def select(self, report):
        if report.invoice_type == 'not':
            p_qty = "pol.product_qty AS po_qty,"
        else:
            p_qty = "sum(pol.product_qty) AS po_qty,"

        if report.report_type == 'summary':
            select_sql = """
                         SELECT
                            rp.name AS supplier,
                            pt.name AS product,
                            pc.name as categ,
                            pt.type AS type,
                            sum(pol.product_qty) AS po_qty,
                            uom2.name AS po_uom,
                            CASE WHEN sum(ail.quantity) IS NOT NULL 
                            THEN sum(ail.quantity) ELSE 0 END AS inv_qty,
                            uom.name AS inv_uom
                         """
        else:
            select_sql = """
                         SELECT 
                            rp.name AS supplier,
                            pt.name AS product,
                            pc.name AS categ,
                            pt.type AS type,
                            po.name AS po_num,
                            {product_qty}
                            uom2.name AS po_uom,
                            ai.number AS inv_no,
                            ai.reference AS bill_ref,
                            CASE WHEN ail.quantity IS NOT NULL 
                            THEN ail.quantity ELSE 0 END as inv_qty,
                            uom.name AS inv_uom
                         """.format(product_qty=p_qty)
        return select_sql

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
            'invoice_type': '',
        }

        # Getting product_template_id from wizard and convert to sql where clause
        product_tmpl_ids = report.product_ids or self.get_product(report)
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
        else:
            wheres['product_ids'] = "AND pol.product_id = NULL"

        if wheres['partner_ids']:
            wheres['partner_ids'] = "AND po.partner_id = ANY (VALUES %s)" % \
                                    wheres['partner_ids']

        if report.invoice_type == 'partial':
            wheres['invoice_type'] = "AND pol.qty_invoiced > 0 AND " \
                                     "pol.product_qty != pol.qty_invoiced"
        else:
            wheres['invoice_type'] = "AND pol.qty_invoiced = 0"

        where_clause = """
                       WHERE
                            po.state IN ('purchase','done')
                            AND po.date_order BETWEEN '{start_date}' AND '{end_date}'
                            {product_ids}
                            {partner_ids}
                            {invoice_type}
                       """.format(**wheres)
        return where_clause

    def group_by(self, report):
        group_by_sql = ''
        if report.report_type == 'summary':
            group_by_sql = """
                          GROUP BY
                            rp.name,
                            pt.name,
                            pc.name,
                            pt.type,
                            uom2.name,
                            uom.name
                          """
        elif report.report_type == 'detail' \
                and report.invoice_type == 'partial':
            group_by_sql = """
                          GROUP BY
                            rp.name,
                            pt.name,
                            pc.name,
                            pt.type,
                            po.name,
                            ai.number,
                            ai.reference,
                            uom2.name,
                            ail.quantity,
                            uom.name
                          """

        return group_by_sql

    def get_product(self, report):
        product_type = []
        if report.type_stockable:
            product_type.append('product')
        if report.type_consumable:
            product_type.append('consu')
        if report.type_service:
            product_type.append('service')

        # filter product id based on:
        # 1) all
        # 2) product type only
        # 3) product category only
        # 4) both type and category
        if report.product_categ_ids and product_type:
            product_ids = self.env['product.template'].search(['&', (
                'categ_id', 'child_of',
                [x.id for x in report.product_categ_ids]),
                                                ('type', 'in', product_type)])
        elif not report.product_categ_ids:
            product_ids = self.env['product.template'].search(
                [('type', 'in', product_type)])
        elif not product_type:
            product_ids = self.env['product.template'].search([(
                'categ_id', 'child_of',
                [x.id for x in report.product_categ_ids])])
        else:
            product_ids = self.env['product.template'].search([])

        return product_ids
