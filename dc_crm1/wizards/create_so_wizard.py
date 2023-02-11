# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
from datetime import timedelta
from odoo.addons import decimal_precision as dp


class CreadSOLineWizard(models.TransientModel):
    _name = "create.so.line.wizard"
    _inherit = 'sol.mixin'
    _description = "create.so.line.wizard"

    # company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, readonly=True)
    # currency_id = fields.Many2one(related='order_id.currency_id', store=True, string='Currency', readonly=True)
    name = fields.Text(string='Description')
    create_so_wizard_id = fields.Many2one('create.so.wizard')
    order_id = fields.Many2one('crm.lead', string='Order Reference',
        required=True, ondelete='cascade', index=True, copy=False)
    crm_product_line_id = fields.Many2one('crm.lead', string='Dòng cơ hội gốc', ondelete='cascade', required=True)
    qty_done = fields.Float(related='crm_product_line_id.qty_done', store=True)
    qty_remain = fields.Float(related='crm_product_line_id.qty_remain', store=True)
    select_categ_id  = fields.Many2one(related='crm_product_line_id.select_categ_id', store=True, string='Chọn Nhóm SP')
    # categ_id = fields.Many2one('product.category', string='Nhóm SP')
    # categ_id = fields.Many2one(related='crm_product_line_id.categ_id', store=True, string='Nhóm SP')



    @api.model
    def default_get(self, fields):
        res = super(CreadSOLineWizard, self).default_get(fields)
        # active_id = self.env['omicall.history'].browse(self._context.get('active_ids')[:1])
        res.update({
            'order_id': self._context.get('active_id') or False,
        #    'phone_number': active_id.destination_number,
        #    'partner_ids':active_id.partner_ids.ids
        })
        return res


    @api.onchange('crm_product_line_id')
    def _onchange_crm_product_line_id(self):
        fns = ['name', 'product_id','categ_id', 'product_uom_qty','product_uom','price_unit','tax_id']
        for r in self:
            for fn in fns:
                r[fn] = r.crm_product_line_id[fn]

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })




class CreadSOWizard(models.TransientModel):
    _name = "create.so.wizard"
    _description = "create.so.wizard"

    crm_id = fields.Many2one('crm.lead', string='CRM', readonly=True)
    line_ids = fields.One2many('create.so.line.wizard','create_so_wizard_id')
    sale_order_id = fields.Many2one('sale.order', readonly=True, string='Đơn hàng được tạo')
    
    @api.model
    def default_get(self, fields):
        res = super(CreadSOWizard, self).default_get(fields)
        crm_id = self._context.get('active_id') or False
        res.update({
            'crm_id': crm_id,
        })
        return res

    def open_so(self):
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env.ref('base.edit_menu_access').sudo().id
        action_id = self.env.ref('sale.action_orders').sudo().id
        model = 'sale.order'
        # http://localhost:8069
        return {
                'type': 'ir.actions.act_url',
                # 'url': 'http://localhost:8069/web?debug=1#id=%s&action=153&model=crm.lead&view_type=form&menu_id=111'%self.crm_id.id,
                'url': '{url}/web?debug=1#id={id}&action={action_id}&model={model}&view_type=form&menu_id={menu_id}'.
                    format(url=url,id=self.sale_order_id.id, model=model, menu_id=menu_id, action_id=action_id),
                'target': 'new',
                'target_type': 'public',
                'res_id': self.sale_order_id.id,
            }

    def action_create_so(self, is_action_confirm=True):   
        sale_vals = {}
        order_line_vals = []
        for i in self.line_ids:
            if not i.product_id:
                continue
            i_va = i.copy_data()[0]
            i_va['name'] = i.product_id.name
            i_va['crm_product_line_id'] = i.crm_product_line_id.id
            i_val = (0,0,i_va )
            order_line_vals.append(i_val)
        if self.crm_id.order_id:
            opportunity_id = self.crm_id.order_id
        else:
            opportunity_id = self.crm_id
        sale_vals['partner_id'] = self.crm_id.partner_id.id
        sale_vals['opportunity_id'] = opportunity_id.id
        sale_vals['user_id'] = self.crm_id.user_id.id
        sale_vals['order_line'] = order_line_vals
        sale_vals['commitment_date'] = fields.Date.context_today(self) + timedelta(days=1)
        sale_vals['payment_term_id'] = 1
        sale_vals['payment_method_id'] = 1
        sale_vals['client_order_ref'] = 'a'
        so = self.env['sale.order'].create(sale_vals)
        if is_action_confirm:
            so.action_confirm()
        self.sale_order_id = so
        action = self.env.ref('dc_crm1.create_so_wizard_action').sudo().read()[0]
        action['res_id'] = self.id
        return action

    def action_create_quotation(self):
        return self.action_create_so(is_action_confirm=False)

        