# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import safe_eval
from datetime import timedelta

class CreatePartnerCrmWizard(models.TransientModel):
    _name = "create.partner.crm.wizard"
    _description = "create.partner.crm.wizard"

    call_id = fields.Many2one('omicall.history')
    contact_name = fields.Char('Tên liên hệ')
    phone_number = fields.Char(string='SĐT', related='call_id.destination_number')
    phone_type = fields.Selection([('phone','Phone'),('mobile','Mobile')], default='mobile')
    is_invisible_phone_type = fields.Boolean(compute='_compute_is_invisible_phone_type')

    @api.depends('create_contact_type_id')
    def _compute_is_invisible_phone_type(self):
        for r in self:
            if r.create_contact_type_id.code in ('create_lead', 'create_contact'):
                r.is_invisible_phone_type = False
            else:
                r.is_invisible_phone_type = True

    message = fields.Text()
    active_ids = fields.Char(default = lambda self: self._context.get('active_ids'))
    create_contact_type_id = fields.Many2one('dc.selection', string='Hành động')
    dc_selection_ids = fields.Many2many('dc.selection', compute='_compute_dc_selection_ids')
    # select_partner_ids = create_contact_type_idfields.Many2many('res.partner', string='Chọn khách hàng để tạo cơ hội', domain="[('id','in',look_partner_ids)]",
    #      help='Trong trường hợp có nhiều hơn khách hàng tương ứng với số điện thoại này')#, default=default_partner_ids
    # len_partner_ids = fields.Integer(compute='_compute_len_partner_ids', )
    # partner_id = fields.Many2one('res.partner', compute='_compute_partner_id')
    select_partner_id = fields.Many2one('res.partner',string='Chọn khách hàng để tạo cơ hội', domain="[('id','in',look_partner_ids)]")
    is_has_partner = fields.Boolean(compute='_compute_is_has_partner')
    # look_partner_ids = fields.Many2many('res.partner','create_partner_partner_rel','partner_id','wizard_id', related='call_id.partner_ids', store=True)
    look_partner_ids = fields.Many2many('res.partner', compute='_compute_is_has_partner', string='Khách hàng ứng với SĐT')
    crm_id = fields.Many2one('crm.lead', readonly=True, string='Cơ hội vừa được tạo')
    lead_id = fields.Many2one('crm.lead', readonly=True, string='Tiềm năng vừa được tạo')
    len_look_partner = fields.Integer(compute='_compute_is_has_partner')
    updated_partner_id = fields.Many2one('res.partner', string='Khách hàng được cập nhập')

    is_show_create_contact_button = fields.Boolean(compute='_compute_is_show_create_contact_type_button')
    is_show_update_contact_button = fields.Boolean(compute='_compute_is_show_create_contact_type_button')
    is_show_create_crm_button = fields.Boolean(compute='_compute_is_show_create_contact_type_button')
    is_show_create_lead_button = fields.Boolean(compute='_compute_is_show_create_contact_type_button')

    @api.depends('create_contact_type_id')
    def _compute_is_show_create_contact_type_button(self):
        if self.create_contact_type_id.code in ('create_contact',):
            self.is_show_create_contact_button = True
        elif self.create_contact_type_id.code in ('update_phone','update_phone2','update_mobile','create_sub_phone','create_sub_mobile','update_mobile2','update_mobile3',):
            self.is_show_update_contact_button = True
        elif self.create_contact_type_id.code in ('create_crm',):
            self.is_show_create_crm_button = True
   
    
    @api.model
    def default_get(self, fields):
        res = super(CreatePartnerCrmWizard, self).default_get(fields)
        active_id = self.env['omicall.history'].browse(self._context.get('active_ids')[:1])
        res.update({
            'call_id': active_id.id,
           'select_partner_id': active_id.partner_ids and active_id.partner_ids[0].id or False
        })
        return res

    def gen_dc_selection_vals(self):
        ids = []
        if self.select_partner_id:
            ids.append('create_crm')
        else:
            if self.contact_name:
                ids.append('create_lead')
                ids.append('create_contact')
            elif self.updated_partner_id:
                if not self.updated_partner_id.phone:
                    ids.append('update_phone')
                elif self.updated_partner_id.phone  and not  self.updated_partner_id.phone2:
                    ids.append('update_phone2')
                if not self.updated_partner_id.mobile:
                    ids.append('update_mobile')
                elif self.updated_partner_id.mobile and not self.updated_partner_id.mobile2:
                    ids.append('update_mobile2')
                elif self.updated_partner_id.mobile and self.updated_partner_id.mobile2 and  not self.updated_partner_id.mobile3:
                    ids.append('update_mobile3')
                # ids.append('create_sub_phone')
                # ids.append('create_sub_mobile')
        return ids        
        
    @api.depends('call_id','select_partner_id', 'updated_partner_id', 'contact_name')
    def _compute_dc_selection_ids(self):
        ids = self.gen_dc_selection_vals()
        self.dc_selection_ids = self.env['dc.selection'].search([('code','in',ids)])
   
    @api.onchange('call_id', 'updated_partner_id', 'contact_name')
    def onchange_updated_partner_id(self):
        self.create_contact_type_id = self.dc_selection_ids[:1]

    @api.depends('call_id')
    def _compute_is_has_partner(self):
        for r in self:
            r.look_partner_ids = r.call_id.partner_ids
            r.is_has_partner = bool(r.look_partner_ids)
            r.len_look_partner = len(r.look_partner_ids)
    
    def create_crm(self):
        partner = self.select_partner_id
        crm = self.env['crm.lead'].create({
            'partner_id':partner.id,
            'type':'opportunity'
        })
        crm.onchange_partner_id()
        self.crm_id = crm
        action = self.env.ref('omicall_api.create_partner_crm_wizard_action').sudo().read()[0]
        action['res_id'] = self.id
        return action

    def create_phone_dict(self):
        return {self.phone_type: self.phone_number}
    
    def create_lead(self):
        vals = self.create_phone_dict()
        vals.update({
            'type':'lead',
            'contact_name':self.contact_name
        })
        crm = self.env['crm.lead'].create(vals)
        self.lead_id = crm
        action = self.env.ref('omicall_api.create_partner_crm_wizard_action').sudo().read()[0]
        action['res_id'] = self.id
        return action

    def create_partner(self):
        vals = self.create_phone_dict()
        vals.update({
                    'name': self.contact_name,
                })
        partner = self.env['res.partner'].create(vals)
        return partner

    def action_confirm(self):# tạo contact hoặc cơ hội
        # if not self.contact_name and not self.updated_partner_id:
        #     raise UserError('Trường điện thoại phụ hoặc tên đối tác phải có giá trị')
        if self.create_contact_type_id.code == 'create_crm':
            self.create_crm()
        elif self.create_contact_type_id.code == 'create_lead':
            self.create_lead()
        else:
            if self.create_contact_type_id.code == 'create_contact':
                if not self.contact_name:
                    raise UserError('Trường Tên liên hệ phải có giá trị')
                partner = self.create_partner()
            elif self.updated_partner_id:
                partner = self.updated_partner_id
                if self.create_contact_type_id.code in ('create_sub_phone', 'create_sub_mobile') :# or self.:#create_sub_mobile
                    fname = 'phone' if self.create_contact_type_id.code =='create_sub_phone' else 'mobile'
                    self.updated_partner_id.write({
                        'child_ids':[(0,0, {'type':'phone', fname: self.phone_number})]
                    })
                elif self.create_contact_type_id.code == 'update_phone':
                    partner.phone = self.phone_number
                elif self.create_contact_type_id.code == 'update_phone2':
                    partner.phone2 = self.phone_number
                elif self.create_contact_type_id.code == 'update_mobile':
                    partner.mobile = self.phone_number
                elif self.create_contact_type_id.code == 'update_mobile2':
                    partner.mobile2 = self.phone_number
                elif self.create_contact_type_id.code == 'update_mobile3':
                    partner.mobile3 = self.phone_number
            # self.create_contact_type_id = self.env.ref('dc_crm1.dc_selection_0')
            self.create_contact_type_id = self.env['dc.selection'].search([('code','=','create_crm')])
            # self.select_partner_ids = partner
            self.select_partner_id = partner
        # action = self.env.ref('omicall_api.create_partner_crm_wizard_action').sudo().read()[0]
        # action['res_id'] = self.id
        # return action
        return self.refresh()
        
    def refresh(self):
        action = self.env.ref('omicall_api.create_partner_crm_wizard_action').sudo().read()[0]
        action['res_id'] = self.id
        return action

    def _open_crm(self, crm_id=None):
        crm_id = crm_id or self.crm_id.id
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env.ref('crm.crm_menu_root').sudo().id
        # action = self.env.ref('crm.crm_lead_opportunities_tree_view').sudo().read()[0]
        action = self.env.ref('omicall_api.crm_lead_opportunities_form_view').sudo().read()[0]
        action_id = action['id']
        
        # if 1:
        #     action['target'] = 'new'
        #     action['res_id'] = False
        #     action['context'] = {'default_phone':self.phone_number, 'default_partner_id': self.select_partner_id.id, 'default_type': 'opportunity'}
        #     return action

        # return rt
        # http://localhost:8069
        return {
                'type': 'ir.actions.act_url',
                # 'url': 'http://localhost:8069/web?debug=1#id=%s&action=153&model=crm.lead&view_type=form&menu_id=111'%self.crm_id.id,
                # 'url': '{url}/web?debug=1#id={id}&action={action_id}&model=crm.lead&view_type=form&menu_id={menu_id}'.format(url=url,id=self.crm_id.id,menu_id=menu_id, action_id=action_id),
                'url': '{url}/web#id={id}&action={action_id}&model=crm.lead&view_type=form&menu_id={menu_id}'.format(url=url, id=crm_id, menu_id=menu_id, action_id=action_id),
                'target': 'new',
                'target_type': 'public',
                'res_id': self.crm_id.id,
                'context':{'default_partner_id': self.select_partner_id.id}
            }
    def open_crm(self):
        crm_id =self.crm_id.id
        return self._open_crm(crm_id)

    def open_lead(self):
        lead_id =self.lead_id.id
        return self._open_crm(lead_id)
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env.ref('crm.crm_menu_root').sudo().id
        action = self.env.ref('crm.crm_lead_all_leads').sudo().read()[0]
        action_id = action['id']
        
        # if 1:
        #     action['target'] = 'new'
        #     action['res_id'] = False
        #     action['context'] = {'default_phone':self.phone_number, 'default_partner_id': self.select_partner_id.id, 'default_type': 'opportunity'}
        #     return action
        # return rt
        # http://localhost:8069
        return {
                'type': 'ir.actions.act_url',
                # 'url': 'http://localhost:8069/web?debug=1#id=%s&action=153&model=crm.lead&view_type=form&menu_id=111'%self.crm_id.id,
                # 'url': '{url}/web?debug=1#id={id}&action={action_id}&model=crm.lead&view_type=form&menu_id={menu_id}'.format(url=url,id=self.crm_id.id,menu_id=menu_id, action_id=action_id),
                'url': '{url}/web#id={id}&action={action_id}&model=crm.lead&view_type=form&menu_id={menu_id}'.format(url=url,id=self.lead_id.id, menu_id=menu_id, action_id=action_id),
                'target': 'new',
                'target_type': 'public',
                'res_id': self.crm_id.id,
                'context':{'default_partner_id': self.select_partner_id.id}
            }

    def open_partner(self):
        url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env.ref('contacts.menu_contacts').sudo().id
        action= self.env.ref('omicall_api.partner_form_action').sudo().read()[0]
        # action['res_id'] = self.select_partner_id.id
        # action['view_id'] = self.env.ref('base.view_partner_form').id
        # action['view_mode'] = 'form'
        # action['target'] = 'new'# là full screen mới
        # return action
        action_id = action['id']
        return {
                'type': 'ir.actions.act_url',
                # 'url': 'http://localhost:8069/web?debug=1#id=%s&action=153&model=crm.lead&view_type=form&menu_id=111'%self.crm_id.id,
                'url': '{url}/web?debug=1#id={id}&action={action_id}&model=res.partner&view_type=form&menu_id={menu_id}'.format(url=url,id=self.select_partner_id.id,menu_id=menu_id, action_id=action_id),
                'target': 'new',
                'target_type': 'public',
                'res_id': self.select_partner_id.id,
            }


    

        