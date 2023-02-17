# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import requests
import json
from odoo.addons.base.models.ir_ui_view import keep_query
from datetime import datetime, timedelta, MINYEAR, date
import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner','mail.thread']

    dc_crm_ids = fields.One2many('crm.lead', 'partner_id', string='Crm')
    sale_summary = fields.Text(compute='_compute_sale_summary', store=True, track_visibility='onchange', readonly=False)
    phone = fields.Char(track_visibility='onchange', required=False)
    omiid = fields.Char(string='omi id', track_visibility='onchange')
    omi_log_ids  = fields.One2many('omi.log','res_id', domain=[('model','=','res.partner')], context={'default_model': 'res.partner'})
    # type = fields.Selection(selection_add=[('phone','SĐT khác')] )
    is_duplicate_phone = fields.Boolean(search='_search_is_duplicate_phone', store=False)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ResPartner, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        return res
    @api.depends('sale_order_ids.state')
    def _compute_sale_summary(self):
        for r in self:
            # so_len = len(r.sale_order_ids.filtered(lambda i: i.state=))
            sale_orders = self.env['sale.order'].search([('partner_id','=', r.id),('state','not in',('draft','cancel'))], order='date_order desc')
            sale_order = sale_orders[:1]
            date_order = sale_order.date_order and sale_order.date_order.strftime('%d/%m/%Y')
            sale_summarys =[]
            if sale_orders:
                msg1 = 'Số lượng SO: %s'%len(sale_orders)
                sale_summarys.append(msg1)
            if date_order:                  
                sale_summarys.append('Ngày order gần nhất: %s'%date_order)
            
            if sale_summarys:
                r.sale_summary = ','.join(sale_summarys)
            else:
                r.sale_summary = False


    def _search_is_duplicate_phone(self, operator, value):
        query = """
                        SELECT id
                        FROM   res_partner p
                        WHERE  EXISTS (
                           SELECT FROM res_partner p2
                           WHERE  p2.phone = p.phone and p.phone is not null
                           AND    p2.id <> p.id
                        );
                    """
        self.env.cr.execute(query, ())
        overlap_mapping = [row[0] for row in self.env.cr.fetchall()]
        if operator == '=' and value == True:
            return [('id', 'in', overlap_mapping)]
        elif operator == '=' and value == False:
            return [('id', 'not in', overlap_mapping)]
        else:
            return [('id', 'in', [])]
    

    @api.model
    def create(self, vals):# trường hợp này có khi thằng con nó được tạo lúc ghi. thằng con được tạo mới thì nó được thằng cha lo rồi.
        partners = super(ResPartner, self.with_context(is_dc_creating_partner=True)).create(vals)
        if not self._context.get('is_dc_creating_partner'):
            OH = self.env['omicall.history']
            for partner in partners:
                data_phone, data_mail = OH.gen_phone_vals(partner)
                if data_phone and partner.type in ('contact',):
                    OH.omi_create(partner)
                elif data_phone and partner.type in ('phone',):
                    OH.omi_edit(partner)
        return partners

    def get_obj_by_fields(self, fnames):
        return [{fname:i[fname] for fname in fnames} for i in self]

    def get_dict_by_fields(self, vals, fnames):
        return {fname:vals.get(fname, False) for fname in fnames }

    @api.multi
    def write(self, vals):# trường hợp này thằng con chỉ có write mà ko có create.
        OH = self.env['omicall.history']
        not_pass_context = False
        z = set(vals).intersection({'name', 'phone','mobile','mobile2','mobile3'})
        if z:#not set(vals).isdisjoint({'name', 'phone','mobile'}):
            if not self._context.get('is_dc_creating_partner'):
                obj_dict_list = self.get_obj_by_fields(z)
                fields_vals = self.get_dict_by_fields(vals, z)
                write_rs = super(ResPartner, self.with_context(is_dc_creating_partner=True)).write(vals)
                OH.omi_edits(self, vals=vals, obj_dict_list=obj_dict_list, fields_vals=fields_vals)
            else:
                not_pass_context = True
        else: 
            not_pass_context = True
        if not_pass_context:
            write_rs = super(ResPartner, self).write(vals)
        return write_rs

    # @api.multi
    # def unlink(self):
    #     unlink_phone = self.filtered(lambda i: i.type=='phone')
    #     parent_partners = unlink_phone.mapped('parent_id')
    #     rs = super(ResPartner, self).unlink() 
    #     OH = self.env['omicall.history']
    #     OH.omi_edits(parent_partners)
    #     return rs

    @api.model
    def cronjob_send_summary_partner_every_day(self):
        print ('1111'*100)
    
   