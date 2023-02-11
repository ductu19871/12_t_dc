# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from datetime import datetime, date
from odoo.tools.misc import formatLang, format_date
import logging
from odoo.exceptions import UserError
from odoo import SUPERUSER_ID
_logger = logging.getLogger(__name__)



####################LS xúc tiến############

#############CRM.LEAD###############
class CL(models.Model):
    _name = 'crm.lead'
    _inherit = ['crm.lead','sol.crm.mixin']
    # _sql_constraints = [
    #     ('crm_line_uniq', 'unique (order_id, product_id, select_categ_id)', 'order_id, product_id,select_categ_id must be unique !')]

    product_uom_qty = fields.Float(string='Ordered Quantity', 
        digits=dp.get_precision('Product Unit of Measure'), store=True, required=True, default=1.0, compute='_compute_product_uom_qty',readonly=False)
    partner_parent_id = fields.Many2one('res.partner')
    is_create_partner_parent_id = fields.Boolean()

    @api.onchange('partner_name')
    def _onchange_to_partner_parent_id(self):
        RP = self.env['res.partner']
        for r in self:
            r.partner_parent_id = r.partner_name and RP.search([('name','=',r.partner_name)])[:1]

    @api.depends('order_line.product_uom_qty')
    def _compute_product_uom_qty(self): 
        for r in self:
            if r.order_line:
                r.product_uom_qty = sum(r.order_line.mapped('product_uom_qty'))# gọi lại chính hàm này nên mấy thằng con bằng 1
            else:
                r.product_uom_qty = 1.0

    a1 = fields.Integer(compute='_compute_a1', store=True, readonly=False)
    
    @api.depends('b1')
    def _compute_a1(self):
        for r in self:
            r.a1 = r.b1
    
    # @api.depends('stage_id')
    # def _compute_a1(self):
    #     for r in self:
    #         r.a1 = int(r.stage_id.sequence)
    

    b1 = fields.Integer()
    
    # def write(self, vals):
    #     rs =  super(CL, self).write(vals)
    #     if 'stage_id' in vals:
    #         for r in self:
    #             if r.type2 =='parent':
    #                 raise UserError('không được thiết lập stage khi là cha')
    #     return rs
    
    # @api.constrains('stage_id')
    # def aldskf(self):
    #     for r in self:
    #         if r.stage_id and r.type2=='parent':
    #             raise UserError('dsfdfd')
    note = fields.Char(string='Ghi chú')
    sol_ids = fields.One2many('sale.order.line', 'crm_product_line_id')
    type2 = fields.Selection([('child','Con'), ('parent','Cha'), ('independ', 'Lẻ')], string='Loại quan hệ', compute='_compute_type2', store=True)
    confirmed_sale_number = fields.Integer(compute='_compute_sale_amount_total', string="Number of Quotations")
    quotation_amount_total = fields.Monetary(compute='_compute_sale_amount_total', string="Sum of Orders", help="Untaxed Total of Confirmed Orders", currency_field='company_currency')
    @api.depends('order_ids')
    def _compute_sale_amount_total(self):
        for lead in self:
            total = 0.0
            quotation_amount_total = 0
            nbr = 0
            confirmed_sale_number = 0
            if lead.order_line or not lead.order_id:
                order_ids = lead.order_ids
            else:
                order_ids = lead.sol_ids.mapped('order_id')
            company_currency = lead.company_currency or self.env.user.company_id.currency_id
            for order in order_ids:
                if order.state in ('draft', 'sent'):
                    nbr += 1
                    quotation_amount_total += order.currency_id._convert(
                        order.amount_untaxed, company_currency, order.company_id, order.date_order or fields.Date.today())
                # if order.state not in ('draft', 'sent', 'cancel'):
                if order.state  in ('done', 'sale'):
                    total += order.currency_id._convert(
                        order.amount_untaxed, company_currency, order.company_id, order.date_order or fields.Date.today())
                    confirmed_sale_number +=1
            lead.sale_amount_total = total
            lead.sale_number = nbr
            lead.confirmed_sale_number = confirmed_sale_number
            lead.quotation_amount_total = quotation_amount_total


    @api.depends('order_line','order_id')
    def _compute_type2(self):
        for r in self:
            r.type2  = r.order_line and 'parent' or r.order_id and 'child' or 'independ' 
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency", readonly=True, store=True, compute_sudo=True)
    ###################so mminx


    ############ product line#########
    order_line_ids = fields.One2many('sale.order.line', 'crm_product_line_id' )
    qty_done = fields.Float(compute='_compute_qty_done', string='Số lượng đã tạo đơn hàng', store=True, 
        digits=dp.get_precision('Product Unit of Measure'))
    qty_remain = fields.Float(compute='_compute_qty_remain', store=True, digits=dp.get_precision('Product Unit of Measure'), string='Số lượng còn lại')
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency", readonly=True, store=True, compute_sudo=True)
    so_price_total = fields.Float(compute='_compute_so_price_total', store=True, string='Doanh thu')
    so_price_unit = fields.Float(compute='_compute_so_price_total', store=True,  string='Đơn giá ở đơn hàng')
    select_categ_id  = fields.Many2one('product.category', string='Chọn Nhóm SP')
    # partner_id = fields.Many2one('res.partner', related='order_id.partner_id')

    @api.depends('order_line.so_price_total','order_line_ids.state', 'order_line_ids.price_total')
    def _compute_so_price_total(self):
        for r in self:
            if not r.order_line:
                order_line_ids = r.order_line_ids.filtered(lambda i: i.state in ('sale','done'))
                r.so_price_total = order_line_ids and sum(order_line_ids.mapped('price_total'))
                r.so_price_unit = order_line_ids and sum(order_line_ids.mapped('price_unit'))/len(order_line_ids)
            else:
                r.so_price_total  = sum(r.order_line.mapped('so_price_total'))
    #  def _compute_quantity(self, qty, to_unit, round=True, rounding_method='UP', raise_if_failure=True):
    @api.depends('order_line.qty_done','order_line_ids.state','order_line_ids.product_uom_qty','order_line_ids.product_uom','product_uom')
    def _compute_qty_done(self):
        for r in self:
            if not r.order_line:
                order_line_ids = r.order_line_ids.filtered(lambda i: i.state in ('sale','done'))
                qty_done = 0.0
                for l in order_line_ids:
                    qty = l.product_uom._compute_quantity(l.product_uom_qty, r.product_uom)
                    qty_done +=qty
                r.qty_done = qty_done
            else:
                r.qty_done = sum(r.order_line.mapped('qty_done'))

    @api.depends( 'product_uom_qty','qty_done')
    def _compute_qty_remain(self):
        for r in self:
            r.qty_remain = r.product_uom_qty - r.qty_done
    is_win = fields.Boolean(compute='_compute_win_state', store=True)
    select_categ_id  = fields.Many2one('product.category', string='Chọn Nhóm SP')
    
    ############ !product line#########
    stage_id = fields.Many2one('crm.stage', compute='_compute_stage_id', store=True, readonly=False)
    @api.depends('win_state', 'order_line.stage_id')
    def _compute_stage_id(self):
        default_stage_id = self._default_stage_id()
        win_stage = self.env.ref('dc_crm1.stage_11')
        for r in self:
            if r.win_state == 'full_win':
                r.stage_id = win_stage
            else:
                if r.order_line:
                    r.stage_id = r.order_line.mapped('stage_id').sorted(lambda i: -i.sequence)[:1]
                else:
                    r.stage_id = default_stage_id
    
    probability_id = fields.Many2one('dc.selection', domain=[('type','=', 'probability_id')], string='Trạng thái xác suất')
    type = fields.Selection(compute='_compute_type', store=True)
    
    probability = fields.Integer(compute='_compute_probability', store=True, inverse='_set_probability_id')

    @api.depends('probability_id')
    def _compute_probability(self):
        for r in self:
            r.probability = r.probability_id.value

    def _set_probability_id(self):
        ds = self.env['dc.selection'].search([])
        ds_val = {i.value: i.id for i in ds }
        for r in self:
            r.probability_id = ds_val.get(r. probability)

    @api.depends('partner_id')
    def _compute_type(self):
        for r in self:
            r.type = 'opportunity' if r.partner_id else 'lead'

    connection_ids = fields.One2many('crm.connection', 'crm_id', string='LS xúc tiến')
    parent_connection_ids = fields.One2many('crm.connection', 'parent_crm_id', string='LS xúc tiến')
    name = fields.Text(compute='_compute_name', store=True, required=False)
    sale_order_ids = fields.Many2many('sale.order', compute='_compute_sale_order_ids')
    call_history_ids = fields.Many2many('omicall.history', compute="_compute_call_history_ids")
    order_line = fields.One2many('crm.lead','order_id')
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency", readonly=True, store=True, compute_sudo=True)
    # currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    planned_revenue = fields.Monetary(compute='_compute_planned_revenue', store=True)

    # amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', track_visibility='onchange', track_sequence=5)
    # amount_by_group = fields.Binary(string="Tax amount by group", compute='_amount_by_group', help="type: [(name, amount, base, formated amount, formated base)]")
    # amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    
    # price_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', track_visibility='always', track_sequence=6)
    # so_price_total = fields.Monetary(string='Doanh thu thực tế', store=True, readonly=True, compute='_compute_so_amount_total', track_visibility='always', track_sequence=7)#sẽ bỏ
    value_rate = fields.Float(compute='_compute_value_rate', store=True, string='Chuyển đổi về giá trị')
    qty_rate = fields.Float(compute='_compute_qty_rate', store=True, string='Chuyển đổi về số lượng')
    
    # qty_done = fields.Integer(compute='_compute_sum_qty_done', string='Số lượng thực tế')
    # product_uom_qty = fields.Integer(compute='_compute_sum_product_uom_qty', string='Số lượng dự kiến')
    partner_id = fields.Many2one('res.partner', compute='_compute_partner_id', store=True, readonly=False)
    contact_name = fields.Char(compute='_compute_partner_id', store=True, readonly=False)
    phone = fields.Char(compute='_compute_partner_id', store=True, readonly=False)
    mobile = fields.Char(compute='_compute_partner_id', store=True, readonly=False)
    @api.depends('order_id.partner_id')
    def _compute_partner_id(self):
        for r in self:
            if r.order_id:
                r.partner_id = r.order_id.partner_id
                r._onchange_partner_id()

    @api.depends('so_price_total','price_total')
    def _compute_value_rate(self):
        for r in self:
            r.value_rate = r.price_total and (r.so_price_total/r.price_total)*100
    
    @api.depends('qty_done','product_uom_qty')
    def _compute_qty_rate(self):
        for r in self:
            r.qty_rate = r.qty_done and r.product_uom_qty and (r.qty_done/r.product_uom_qty)*100

    
    win_state = fields.Selection([('full_win', 'Thắng'), ('partly_win', 'Thắng 1 phần'), ('not_win', 'Chưa thắng')], compute='_compute_win_state', store=True, string='Trạng thái thắng')
    @api.depends('qty_done','order_line.win_state')
    def _compute_win_state(self):
        STATE_DEFAULT = 'not_win'
        for r in self:
            if not r.order_line:
                r.is_win = bool(r.qty_done)
                if not r.qty_remain and r.qty_done:
                    r.win_state = 'full_win' 
                elif  r.qty_done:
                    r.win_state = 'partly_win' 
                else:
                    r.win_state = STATE_DEFAULT
            else:
                line_win_states = r.order_line.mapped('win_state')
                if line_win_states:
                    if all(l=='full_win' for l in line_win_states):
                        win_state = 'full_win'
                    elif any(l in ('full_win','partly_win') for l in line_win_states):
                        win_state = 'partly_win'
                    else:
                        win_state = STATE_DEFAULT
                else:
                    win_state = STATE_DEFAULT
                r.win_state = win_state
    # 
    # 
    #      
    # so_price_total = fields.Monetary(string='Doanh thu thực tế', store=True, readonly=True,  track_visibility='always', track_sequence=7)
    
    @api.depends('order_line.product_uom_qty','product_uom_qty')
    def _compute_sum_product_uom_qty(self):
        for r in self:
            if r.order_line:
                r.product_uom_qty = sum(r.order_line.mapped('product_uom_qty'))
            else:
                r.product_uom_qty = r.product_uom_qty
            
    @api.depends('order_line.qty_done','qty_done')
    def _compute_sum_qty_done(self):# số lượng thực tế
        for r in self:
            if r.order_line:
                r.qty_done = sum(r.order_line.mapped('qty_done'))
            else:
                r.qty_done = r.qty_done

    @api.depends('price_total')#'order_line.price_total'
    def _compute_planned_revenue(self):
        for r in self:
            r.planned_revenue = r.price_total

    # @api.depends('order_line.so_price_total','order_line.order_line_ids.state', 'order_line.order_line_ids.price_total', 'order_line.order_line_ids.price_unit')
    @api.depends('order_line.so_price_total','so_price_total')
    def _compute_so_amount_total(self):
        for r in self:
            if r.order_line:
                so_price_total = sum(r.order_line.mapped('so_price_total'))
                r.so_price_total = so_price_total
            else:
                r.so_price_total = r.so_price_total

    @api.depends('partner_id', 'phone', 'order_line','product_id','select_categ_id')
    def _compute_name(self):
        for r in self:
            if r.order_line:
                arr_res = []
                phones = {}
                if r.phone:
                    phones['Phone'] = r.phone
                if r.mobile:
                    phones['mobile'] = r.mobile
                str_phone_mobile = ','.join(['%s:%s'%(k,v) for k,v in phones.items()])

                names = []
                if r.partner_id.display_name:
                    name = r.partner_id.display_name
                elif str_phone_mobile:
                    name = 'Tiềm năng'
                else:
                    name = 'No partner, phone'
                order_line_infos = [i.product_id.name or (i.select_categ_id.name and '*%s'%i.select_categ_id.name)  or '' for i in r.order_line[0:4]]
                order_line_infos = [i for i  in order_line_infos if i]
                order_line_info = ','.join(order_line_infos) + ('...' if (r.order_line and len(r.order_line) or 0 ) > 4 else '')


                total = formatLang(self.env, r.price_total, currency_obj=r.currency_id)
                # name += '|' + order_line_info if order_line_info else ''
                arr_res = [i for i in [name, str_phone_mobile, order_line_info, total] if i]
                r.name = '|'.join(arr_res)
            else:
                name = r.product_id.display_name or r.select_categ_id.display_name or r.note
                r.name = name

    def create_default_create_so_wizard(self):
        line_ids = []
        if self.order_line:
            order_line = self.order_line
            order_id = self
        else:
            order_line = self
            if self.order_id:
                order_id = self.order_id
            else:
                order_id = self
        for line in order_line:
            if not line.qty_remain:
                continue
            line_va = line.copy_data()[0]
            line_va['crm_product_line_id']= line.id
            line_va['order_id']=order_id.id#self.id
            line_va['product_uom_qty']= line.qty_remain if line.qty_remain > 0 else 0
            print ('line_va', line_va)
            line_ids.append((0,0,line_va))

        res = {
            'crm_id': self.id,
            'line_ids':line_ids,
            # 'line_ids':[(0,0,{'order_id':self.id, 'crm_product_line_id': i.id}) for i in self.order_line]
        #    'phone_number': active_id.destination_number,
        #    'partner_ids':active_id.partner_ids.ids
        }
        rs = self.env['create.so.wizard'].create(res)
        # rs.line_ids._onchange_crm_product_line_id()
        return rs.id
    
    def create_sale_wizard(self):
        action = self.env.ref('dc_crm1.create_so_wizard_action').sudo().read()[0]
        action['res_id'] = self.create_default_create_so_wizard()
        return action
    
    # @api.depends('order_line.price_total','price_total')
    # def _amount_all(self):
    #     """
    #     Compute the total amounts of the SO.
    #     """
    #     for order in self:
    #         if order.order_line:
    #             amount_untaxed = amount_tax = 0.0
    #             for line in order.order_line:
    #                 amount_untaxed += line.price_subtotal
    #                 amount_tax += line.price_tax
    #             order.update({
    #                 'amount_untaxed': amount_untaxed,
    #                 'amount_tax': amount_tax,
    #                 'price_total': amount_untaxed + amount_tax,
    #                 # 'planned_revenue': amount_untaxed + amount_tax,
    #             })
    #         else:
    #             order.price_total = order.price_total



    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        # """
        # Update the following fields when the partner is changed:
        # - Pricelist
        # - Payment terms
        # - Invoice address
        # - Delivery address
        # """
        # if not self.partner_id:
        #     self.update({
        #         'partner_invoice_id': False,
        #         'partner_shipping_id': False,
        #         'payment_term_id': False,
        #         'fiscal_position_id': False,
        #     })
        #     return

        # addr = self.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            # 'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            # 'partner_invoice_id': addr['invoice'],
            # 'partner_shipping_id': addr['delivery'],
            # 'user_id': self.partner_id.user_id.id or self.partner_id.commercial_partner_id.user_id.id or self.env.uid
        }
        # if self.env['ir.config_parameter'].sudo().get_param('sale.use_sale_note') and self.env.user.company_id.sale_note:
        #     values['note'] = self.with_context(lang=self.partner_id.lang).env.user.company_id.sale_note

        # if self.partner_id.team_id:
        #     values['team_id'] = self.partner_id.team_id.id

        # if self.user_id.id == values.get('user_id'):
        #     del values['user_id']
        self.update(values)

    @api.depends('partner_id')
    def _compute_sale_order_ids(self):
        for r in self:
            r.sale_order_ids = r.partner_id.sale_order_ids
    
    @api.depends('partner_id')
    def _compute_call_history_ids(self):
        OH = self.env['omicall.history']
        for r in self:
            if r.partner_id:
                phones = OH.gen_phone_vals_only(r.partner_id)
                # phone = r.partner_id.phone
                # mobile =  r.partner_id.mobile
                if phones:
                    r.call_history_ids = self.env['omicall.history'].search([
                        ('destination_number','in', phones),
                        ('transaction_id','!=', False)
                        ])
                else:
                    r.call_history_ids = False
            else:
                r.call_history_ids = False

    @api.multi
    def _create_lead_partner(self):
        #đè
        """ Create a partner from lead data
            :returns res.partner record
        """
        Partner = self.env['res.partner']
        contact_name = self.contact_name
        if not contact_name:
            contact_name = Partner._parse_partner_name(self.email_from)[0] if self.email_from else False

        if self.partner_name and self.is_create_partner_parent_id and not self.partner_parent_id:
            partner_company = Partner.create(self._create_lead_partner_data(self.partner_name, True))
        elif self.partner_parent_id:#thêm
            partner_company = self.partner_parent_id
        # elif self.partner_id:
        #     partner_company = self.partner_id
        else:
            partner_company = None

        if contact_name:
            return Partner.create(self._create_lead_partner_data(contact_name, False, partner_company.id if partner_company else False))

        if partner_company:
            return partner_company
        return Partner.create(self._create_lead_partner_data(self.name, False))


    @api.multi
    def _create_lead_partner_data(self, name, is_company, parent_id=False):
        """ extract data from lead to create a partner
            :param name : furtur name of the partner
            :param is_company : True if the partner is a company
            :param parent_id : id of the parent partner (False if no parent)
            :returns res.partner record
        """
        rs = super()._create_lead_partner_data(name, is_company, parent_id=parent_id)
        rs.update({
            'district_id': self.district_id.id,
            'ward_id': self.ward_id.id,
            'house': self.house,
            'door': self.door,
        })
        return rs
        # email_split = tools.email_split(self.email_from)
        # rs =  {
        #     'name': name,
        #     'user_id': self.env.context.get('default_user_id') or self.user_id.id,
        #     'comment': self.description,
        #     'team_id': self.team_id.id,
        #     'parent_id': parent_id,
        #     'phone': self.phone,
        #     'mobile': self.mobile,
        #     'email': email_split[0] if email_split else False,
        #     'title': self.title.id,
        #     'function': self.function,
        #     'street': self.street,
        #     'street2': self.street2,
        #     'zip': self.zip,
        #     'city': self.city,
        #     'country_id': self.country_id.id,
        #     'state_id': self.state_id.id,
        #     'website': self.website,
        #     'is_company': is_company,
        #     'type': 'contact'
        # }


