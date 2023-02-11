# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.exceptions import UserError
from odoo.osv.expression import AND, expression
from odoo.addons import decimal_precision as dp

from datetime import datetime,date, timedelta
import logging
_logger = logging.getLogger(__name__)
class crmproductlinereport(models.TransientModel):
    _name = 'crm.product.line.report'
    # _inherit = 'tl.common.report'
    _description = 'crmproductlinereport'
    # _auto = False
    # _order = 'date_order asc, price_total asc'

    sum_product_uom_qty = fields.Float(string='Số lượng dự kiến')
    sum_qty_done = fields.Float('SL thực tế')
    rate = fields.Float('Tỉ lệ chuyển đổi SL')
    select_categ_id  = fields.Many2one('product.category', string='Chọn Nhóm SP')
    product_id = fields.Many2one('product.product')
    partner_id = fields.Many2one('res.partner')
    user_id = fields.Many2one('res.users')

    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    price_total = fields.Float( string='Total', readonly=True)
    so_price_total = fields.Float()
    so_price_unit = fields.Float()


    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        if view_type in ('tree','list'):
            print ('***'*10,self._context,  self._context.get('dc_report_wizard_id'))
        res = super(crmproductlinereport, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        return res



    # @api.model_cr
    # def init(self):
    #     # self._table = sale_report
    #     tools.drop_view_if_exists(self.env.cr, self._table)
    #     self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
    #         %s
     
    #         )""" % (self._table, self._select())

    #     )

    # @property
    # def _table_query(self):
    #     ''' Report needs to be dynamic to take into account multi-company selected + multi-currency rates '''
    #     # rs =  '%s %s %s %s' % (self._select(), self._from(), self._where(), self._group_by())
    #     rs = self._select()
    #     print (rs)
    #     return rs
    

    def init_data(self, wizard_id):
        default_groups = ['select_categ_id', 'partner_id', 'product_id', 'user_id']
        select_groups = wizard_id.group_by_ids.mapped('code')
        groups = []
        for i  in default_groups:
            if i in select_groups:
                groups.append(i)
        group_by = ','.join(groups)
        select_group = []
        for i in default_groups:
            if i in groups:
                select_group.append(i)
            else:
                select_group.append('null')
        select_group = ','.join(select_group)
        sql = '''delete from %s where create_uid=%s'''%(self._table, self.env.user.id)
        self._cr.execute(sql)
        # sql = '''
        #     insert into {table}(create_uid, create_date, write_uid, write_date,sum_qty_done, rate, product_id, partner_id, user_id) 
        #     select {uid}, current_timestamp, {uid}, current_timestamp, sum(qty_done) as sum_qty_done,(sum(qty_done)/sum(product_uom_qty)*100)::decimal(16,2) as rate,product_id,cl.partner_id,user_id from crm_product_line cpl
        #     join crm_lead cl on cpl.order_id = cl.id
        #     group by partner_id, product_id, user_id
        # '''.format(table = self._table, uid=self.env.user.id)

        sql = '''
            insert into {table}(create_uid, create_date, write_uid, write_date,sum_product_uom_qty, sum_qty_done, rate, price_unit, {default_groups}) 
            select {uid}, current_timestamp, {uid}, current_timestamp,sum(product_uom_qty) as sum_product_uom_qty, sum(qty_done) as sum_qty_done,
            (sum(qty_done)/sum(product_uom_qty)*100)::decimal(16,2) as rate, (sum(price_unit)/count(*)*100)::decimal(16,2) as price_unit,
            
            {select_group} from crm_product_line cpl
            join crm_lead cl on cpl.order_id = cl.id
            group by {group_by}
        '''.format(table = self._table, uid=self.env.user.id, select_group=select_group, group_by=group_by, default_groups=','.join(default_groups))

        print (sql)
        _logger.info(sql)
        self._cr.execute(sql)
        return sql



    # def _select(self):
    #     res = '''
    #     select row_number() over() as id, sum(qty_done) as sum_qty_done,(sum(qty_done)/sum(product_uom_qty)*100)::decimal(16,2) as rate,product_id,cl.partner_id,user_id from crm_product_line cpl
    #     join crm_lead cl on cpl.order_id = cl.id
    #     group by partner_id, product_id, user_id
    #     '''
    #     return res


