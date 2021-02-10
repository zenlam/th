import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.tools import float_round

logger = logging.getLogger(__name__)


class ThGtoSummaryReport(models.TransientModel):
    _name = 'th.gto.summary.report'
    _description = 'TH Mall Integration GTO Manual Report Wizard'

    date = fields.Date(string="Date")
    from_date = fields.Date(string="From Date")
    outlet_id = fields.Many2one('stock.warehouse', string="Outlet")

    @api.multi
    def export_gto_summary_report(self):
        report_name = 'gto_summary_report'
        report = {
            'type': 'ir.actions.report',
            'report_type': 'qweb-text',
            'report_name': report_name,
            'context': dict(self.env.context),
            'data': {'dynamic_report': True},
        }
        return report

    @api.model
    def get_data(self):
        to_date = self.date
        if self.from_date:
            from_date = self.from_date
        else:
            previous_date = datetime.strptime(
                to_date, '%Y-%m-%d'
            ) - relativedelta(days=1)
            from_date = datetime.strftime(previous_date, '%Y-%m-%d')

        cond = """ where --(po.is_refund <> 'true' AND po.is_refunded <> 'true')
                --and 
                ps.start_at between '{from_date} 21:00:00' and '{to_date} 21:00:00'
                and po.outlet_id = {outlet_id}
            """.format(from_date=from_date, to_date=to_date,
                       outlet_id=self.outlet_id.id)

        sql = """
            select
            COALESCE(sum(round(pol.qty * pol.price_unit, 2) + round(round(pol.qty * pol.price_unit, 2) * (CASE WHEN tax.price_include = FALSE THEN tax.amount / 100 ELSE 0 END), 2)), 0) AS total,
            COALESCE(sum(round(pol.qty * pol.price_unit, 2)) - sum(round(round(pol.qty * pol.price_unit, 2) / (1 + tax.amount / 100) * (CASE WHEN tax.price_include = TRUE THEN tax.amount / 100 ELSE 0 END), 2)), 0) AS before_tax,
            COALESCE(sum(round(round(pol.qty * pol.price_unit, 2) / (1 + CASE WHEN tax.price_include = TRUE THEN tax.amount / 100 ELSE 0 END) * (tax.amount / 100), 2)), 0) AS tax,
            --COALESCE(round(sum(pol.discount_amount + pol.discount_amount * (CASE WHEN tax.price_include = FALSE THEN tax.amount / 100 ELSE 0 END)), 2), 0) AS discount,
            COUNT(DISTINCT po.id) AS ticket_count --,
            --COALESCE(round(sum(pol.discount_amount / (1 + CASE WHEN tax.price_include = TRUE THEN tax.amount / 100 ELSE 0 END)), 2), 0) AS discount_before_tax
            
            from pos_order_line pol
            inner join pos_order po on po.id = pol.order_id
            inner join pos_session ps ON po.session_id = ps.id
            left join account_tax_pos_order_line_rel tax_rel on tax_rel.pos_order_line_id = pol.id
            left join account_tax tax on tax.id = tax_rel.account_tax_id        
            %s
            --and pol.non_sale = FALSE
        """ % cond

        self.env.cr.execute(sql)
        data = self.env.cr.dictfetchall()
        # tax_adjustment = self.get_tax_adjustment(cond)
        # redemption_amount = self.get_redemption_amount(cond)
        # if data:
            # Remove tax adjustment
            # data[0]['tax'] += tax_adjustment
            # data[0]['before_tax'] -= tax_adjustment
            # Remove redemption amount
            # data[0]['total'] -= redemption_amount['total']
            # data[0]['before_tax'] -= redemption_amount['before_tax']
            # data[0]['tax'] -= redemption_amount['tax']
            # data[0]['ticket_count'] -= redemption_amount['ticket_count']
        return data

    # def get_tax_adjustment(self, cond):
    #     self.env.cr.execute("""
    #                 SELECT COALESCE(SUM(tax_adjustment), 0)
    #                 FROM pos_order po
    #                  INNER JOIN pos_session ps ON po.session_id = ps.id
    #                 %s
    #             """ % cond)
    #     data = self.env.cr.fetchone()
    #     if data:
    #         return float(data[0])
    #     return 0

    # def get_redemption_amount(self, cond):
    #     self.env.cr.execute("""
    #         WITH tmp AS (
    #             SELECT
    #             COALESCE(SUM(poslvd.value + poslvd.unredeem_value), 0) AS total,
    #             COALESCE(SUM(round((poslvd.value + poslvd.unredeem_value) / (1 + tax.amount / 100), 2)), 0) AS before_tax,
    #             COALESCE(SUM(poslvd.value + poslvd.unredeem_value), 0) - COALESCE(SUM(round((poslvd.value + poslvd.unredeem_value) / (1 + tax.amount / 100), 2)), 0) AS tax,
    #             CASE WHEN COALESCE(SUM(poslvd.value), 0) >= MAX(po.origin_total) THEN 1 ELSE 0 END AS ticket_count
    #             FROM pos_order po
    #             INNER JOIN pos_order_sale_voucher_detail poslvd ON po.id = poslvd.order_id
    #             INNER JOIN account_account ON poslvd.tax_account_id = account_account.id
    #             INNER JOIN account_tax tax ON account_account.id = tax.account_id
    #             INNER JOIN pos_session ps ON po.session_id = ps.id
    #             %s
    #             GROUP BY poslvd.order_id
    #         ) SELECT
    #             COALESCE(SUM(total), 0)        AS total,
    #             COALESCE(SUM(before_tax), 0)   AS before_tax,
    #             COALESCE(SUM(tax), 0)          AS tax,
    #             COALESCE(SUM(ticket_count), 0) AS ticket_count
    #           FROM tmp;
    #     """ % cond)
    #     data = self.env.cr.dictfetchone()
    #     return data

    @api.model
    def get_cash_data(self):
        from_date = to_date = datetime.strftime(self.date, '%Y-%m-%d')
        if self.from_date:
            previous_date = datetime.strptime(
                self.from_date, '%Y-%m-%d'
            ) + relativedelta(days=+1)
            from_date = datetime.strftime(previous_date, '%Y-%m-%d')
        sql = """
            select  
            COALESCE(sum(round(bank_line.amount,2)), 0) as cash
            
            from pos_session ps
            inner join account_bank_statement bank on bank.id = ps.cash_register_id
            inner join account_bank_statement_line bank_line on bank_line.statement_id = bank.id
            where bank_line.date between '%s' and '%s' 
            --and ps.outlet_id = percent(d) 
            and bank_line.pos_statement_id is not null
        """ % (from_date, to_date)  # (from_date, to_date, self.outlet_id.id)
        self.env.cr.execute(sql)
        data = self.env.cr.dictfetchall()
        return data

    @api.model
    def get_onsite_ticket(self, cond):
        count_onsite = """
            select  
            count(distinct(po.id)) as total_on_site
            
            from pos_order po
            left join pos_session ps ON po.session_id = ps.id
            left join account_bank_statement_line absl on po.id = absl.pos_statement_id
            left join account_journal aj on aj.id =  absl.journal_id
            %s
            --and aj.payment_type = 'on_site' and aj.is_rounding_method = False
        """ % cond
        self.env.cr.execute(count_onsite)
        result = self.env.cr.dictfetchall()
        return result and result[0] or {}

    @api.model
    def get_offsite_ticket(self, cond):
        count_offsite = """
            select  
            count(distinct(po.id)) as total_off_site
            
            from pos_order po
            left join pos_session ps ON po.session_id = ps.id
            left join account_bank_statement_line absl on po.id = absl.pos_statement_id
            left join account_journal aj on aj.id =  absl.journal_id
            %s
            --and aj.payment_type = 'off_site' and aj.is_rounding_method = False
        """ % cond
        self.env.cr.execute(count_offsite)
        result = self.env.cr.dictfetchall()
        return result and result[0] or {}

    @api.model
    def get_total_ticket(self, cond):
        count_ticket = """
            select  
            count(distinct(po.id)) as total_ticket
            
            from pos_order po
            left join pos_session ps ON po.session_id = ps.id
            left join account_bank_statement_line absl on po.id = absl.pos_statement_id
            left join account_journal aj on aj.id =  absl.journal_id
            %s
            --and aj.payment_type in ('on_site','off_site') and aj.is_rounding_method = False
        """ % cond
        self.env.cr.execute(count_ticket)
        result = self.env.cr.dictfetchall()
        return result and result[0] or {}

    @api.model
    def get_total_tax(self, cond):
        total_tax = """
            select 
            COALESCE(sum(round(round(pol.qty * pol.price_unit, 2) / (1 + CASE WHEN tax.price_include = TRUE THEN tax.amount / 100 ELSE 0 END) * (tax.amount / 100), 2)), 0) AS tax
            
            from pos_order_line pol
            inner join pos_order po on po.id = pol.order_id
            inner join pos_session ps ON po.session_id = ps.id
            left join account_tax_pos_order_line_rel tax_rel on tax_rel.pos_order_line_id = pol.id
            left join account_tax tax on tax.id = tax_rel.account_tax_id 
            %s
        """ % cond
        self.env.cr.execute(total_tax)
        result = self.env.cr.dictfetchall()

        return result and result[0] or {}

    @api.model
    def get_onsite_offsite_data(self):
        to_date = datetime.strftime(self.date, '%Y-%m-%d')
        if self.from_date:
            from_date = self.from_date
        else:
            previous_date = datetime.strptime(
                to_date, '%Y-%m-%d'
            ) + relativedelta(days=-1)
            from_date = datetime.strftime(previous_date, '%Y-%m-%d')

        cond = """ 
                where --(po.is_refund <> 'true' AND po.is_refunded <> 'true' )
                --and 
                ps.start_at between '{from_date} 21:00:00' and '{to_date} 21:00:00'
                --and po.outlet_id = {outlet_id}
            """.format(from_date=from_date, to_date=to_date,
                       outlet_id=self.outlet_id.id)
        total_sale_by_payment_sql = """
            select  
            --aj.payment_type as payment_type,
            sum(absl.amount) as total_amount --, 
            --sum(case when aj.payment_type = 'on_site' then absl.amount else 0 end) as on_site_amount,
            --sum(case when aj.payment_type = 'off_site' then absl.amount else 0 end) as off_site_amount,
            --sum(case when aj.payment_type = 'redemption' then absl.amount else 0 end) as redemption_amount,
            --sum(case when aj.payment_type = 'on_site' and aj.is_rounding_method = False then absl.amount else 0 end) as on_site_without_rounding,
            --sum(case when aj.payment_type = 'off_site' and aj.is_rounding_method = False then absl.amount else 0 end) as off_site_without_rounding,
            --sum(case when aj.is_rounding_method = True then absl.amount else 0 end) as total_rounding

            from pos_order po
            left join pos_session ps ON po.session_id = ps.id
            left join account_bank_statement_line absl on po.id = absl.pos_statement_id
            left join account_journal aj on aj.id =  absl.journal_id
            %s
            --group by aj.payment_type
        """ % cond
        self.env.cr.execute(total_sale_by_payment_sql)
        result = self.env.cr.dictfetchall()
        # if len(result) == 0:
        #     raise osv.except_osv(_('Warning!'), _("Report missing data"))
        data = {'all_total': 0, 'total_rounding': 0}
        # for row in result:
        #     if row['payment_type'] == 'on_site':
        #         data['on_site'] = row['on_site_amount']
        #         data['all_total'] += row['on_site_amount']
        #         data['on_site_without_rounding'] = row[
        #             'on_site_without_rounding']
        #     if row['payment_type'] == 'off_site':
        #         data['off_site'] = row['off_site_amount']
        #         data['all_total'] += row['off_site_amount']
        #         data['off_site_without_rounding'] = row[
        #             'off_site_without_rounding']
        #     if row['payment_type'] == 'redemption':
        #         data['redemption'] = row['redemption_amount']
        #         data['all_total'] += row['redemption_amount']
        #     data['total_rounding'] += row['total_rounding']
        tax_data = self.get_total_tax(cond)
        # tax_adjustment = self.get_tax_adjustment(cond)
        cash = self.get_cash_data()[0]['cash'] or 0
        # tax = (tax_data.get('tax') and tax_data['tax'] or 0) + (tax_adjustment)
        # total_net_sale = (data['all_total'] + (data['total_rounding'] * -1)) - tax

        # net_on_site_excl_tax = float_round(
        #     (data.get('on_site') and data['on_site'] or 0.0) / (
        #                 data['all_total'] or 1) * total_net_sale, 2)
        # net_off_site_excl_tax = float_round(
        #     (data.get('off_site') and data['off_site'] or 0.0) / (
        #                 data['all_total'] or 1) * total_net_sale, 2)
        #
        # data['on_site_with_tax'] = data.get('on_site_without_rounding') and \
        #                            data['on_site_without_rounding'] or 0
        # data['off_site_with_tax'] = data.get('off_site_without_rounding') and \
        #                             data['off_site_without_rounding'] or 0
        #
        # data['on_site_without_tax'] = net_on_site_excl_tax
        # data['off_site_without_tax'] = net_off_site_excl_tax
        #
        # data['on_site_tax'] = float_round((data.get(
        #     'on_site_without_rounding') and data[
        #                                        'on_site_without_rounding'] or 0) - net_on_site_excl_tax,
        #                                   2)
        # data['off_site_tax'] = float_round((data.get(
        #     'off_site_without_rounding') and data[
        #                                         'off_site_without_rounding'] or 0) - net_off_site_excl_tax,
        #                                    2)
        #
        # data['cash_wo_tax'] = float_round(
        #     cash / (data['all_total'] or 1) * total_net_sale, 2)
        #
        # onsite_tc_count = self.get_onsite_ticket(cond)
        # data['onsite_tc'] = onsite_tc_count.get('total_on_site') and \
        #                     onsite_tc_count['total_on_site'] or 0
        #
        # offsite_tc_count = self.get_offsite_ticket(cond)
        # data['offsite_tc'] = offsite_tc_count.get('total_off_site') and \
        #                      offsite_tc_count['total_off_site'] or 0
        #
        # total_tc_count = self.get_total_ticket(cond)
        # data['total_tc'] = total_tc_count.get('total_ticket') and \
        #                    total_tc_count['total_ticket'] or 0
        return data
