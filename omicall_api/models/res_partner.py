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
    type = fields.Selection(selection_add=[('phone','SĐT khác')] )
    is_duplicate_ref = fields.Boolean(search='_search_is_duplicate_ref', store=False)

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


    def _search_is_duplicate_ref(self, operator, value):
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
    # is_must_set_omi = fields.Boolean(compute='_compute_is_must_set_omi', store=True)

    # @api.depends('child_ids.mobile,child_ids.mobile')
    # def _compute_is_must_set_omi(self):
    #     for r in self:
    #         for c  in r.child_ids:
    #             is_must_set_omi = False
    #             if c.type =='phone':
    #                 if c.mobile or c.phone:
    #                     is_must_set_omi = True

    # @api.constrains('phone','mobile')
    # def constrains_phone(self):
    #     for r in self:
    #         pass

    #child_ids: thằng con chỉ có tạo mới, sửa
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
        # objs = []
        # for i in self:
        #     objs.append({fname:i[fname] for fname in fnames})

    def get_dict_by_fields(self, vals, fnames):
        return {fname:vals.get(fname, False) for fname in fnames }

    @api.multi
    def write(self, vals):# trường hợp này thằng con chỉ có write mà ko có create.
        OH = self.env['omicall.history']
        not_pass_context = False
        z = set(vals).intersection({'name', 'phone','mobile'})
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

    @api.multi
    def unlink(self):
        unlink_phone = self.filtered(lambda i: i.type=='phone')
        # parent_partners0 = self.mapped('parent_id')
        parent_partners = unlink_phone.mapped('parent_id')
        # for partner in self:
        #     if partner.type =='phone':
        #         print ('ahahaha')
        rs = super(ResPartner, self).unlink() 
        OH = self.env['omicall.history']
        OH.omi_edits(parent_partners)
        # for partner in self:
        #     if partner.type =='phone':
        #         print ('ahahaha')
        # raise UserWarning('ahahS')
        return rs

    # @api.model
    # def create(self, vals):
        
    #     is_send_omi = self._context.get('is_send_omi') or 1
    #     is_send_omi = self.env['ir.config_parameter'].sudo().get_param('omicall_api.is_send_omi')
    #     partners = super(ResPartner, self).create(vals)
    #     if  is_send_omi:
    #         for p in partners:
    #             if p.type =='phone':
    #                 self.env['omicall.history'].omi_create(p)
    #         for p in (is_send_omi and partners or []):
    #             self.env['omicall.history'].omi_create(p)
    #     return partners


    # @api.multi
    # def write(self, vals):
    #     is_send_omi = self._context.get('is_send_omi') or 1
    #     is_send_omi = self.env['ir.config_parameter'].sudo().get_param('omicall_api.is_send_omi')
    #     if not set(vals).isdisjoint({'name', 'phone','mobile'}) and is_send_omi:
    #         for p in self:
    #             old_sdt_asets = [set([sdt for sdt in [p.phone, p.mobile] if sdt]) for p in self]

    #     rs = super(ResPartner, self).write(vals)
    #     if not set(vals).isdisjoint({'name', 'phone','mobile'}) and is_send_omi:
    #         # will_new_omiid
    #         #phone  = False
    #         new_phone_mobile_set = set([i for i in [vals.get('phone'), vals.get('mobile')] if i])
    #         for count, p in enumerate(self):
    #             isdisjoint_phone_old_with_new = new_phone_mobile_set.isdisjoint(old_sdt_asets[count])# nếu ko giống với số điện thoại củ gì cả
    #             self.env['omicall.history'].omi_edit(p, isdisjoint=isdisjoint_phone_old_with_new)
    #     return rs


    

    @api.model
    def cronjob_send_summary_partner_every_day(self):
        print ('1111'*100)
    
    
    # def get_omicall_token(self):
    #     company_id = self.env['res.company'].browse(1)
    #     if company_id:
    #         url = self.env.ref('wine_api.url_get_token').url + company_id.api_key
    #         response = requests.get(url)
    #         ls_json = response.json()
    #         omi_token = ls_json['payload']['access_token']
    #         print ('**omi_token**', omi_token)
    #         company_id.omi_token = omi_token
    #         return omi_token
    
    