# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
from datetime import timedelta
import logging
_logger = logging.getLogger(__name__)
class OmicallWizard(models.TransientModel):
    _name = "omicall.wizard"
    _description = "omicall.wizard"

    message = fields.Text()
    active_ids = fields.Char(default = lambda self: self._context.get('active_ids'))
    active_model = fields.Char(default = lambda self: self._context.get('active_model'))
    type_id = fields.Many2one('dc.selection', domain="[('type','=', active_model)]")

    # @api.onchange('active_model')
    # def _onchange_active_model(self):
    #     vals = []
    #     vals['domain'] = {'type_id':[('type','=', self.active_model)]}
    #     return vals
    # type = fields.Selection([('omi_create','Tạo'),
    #     ('omi_edit','Sửa'), 
    #     ('omi_delete','Delete'), 
    #     ('omi_get', 'omi_get'), ('update_omiid', 'update_omiid'),
    #     ('omi_get_by_omiid', 'omi_get_by_omiid'), ('omi_list', 'omi_list') ,
    #     ('get_call_transaction_list', 'get_call_transaction_list'), 
    #     ('create_call_history', 'create_call_history'), 
    #     ('omi_get_webhook','omi_get_webhook') ,
    #     ('destroy_contact_webhook','destroy_contact_webhook'),
    #     ('destroy_call_webhook', 'destroy_call_webhook'),
    #     ('add_contact_webhook','add_contact_webhook'),
    #     ('add_call_webhook','add_call_webhook'),
    #     ('get_omicall_token', 'get_omicall_token'),
    #     ('webhook_create_contact','webhook_create_contact')], default='update_omiid')
    from_date = fields.Date(default =lambda self: fields.Date.context_today(self) - timedelta(days=1))
    to_date = fields.Date(default=fields.Date.context_today)
    status_code = fields.Integer()
    phone = fields.Char(default=lambda self: self._context.get('active_model') =='res.partner' and  self._context.get('active_ids') and self.env['res.partner'].browse(self._context.get('active_ids')[:1]).phone)
    omiid = fields.Char(default=lambda self: self._context.get('active_model') =='res.partner' and self._context.get('active_ids') and self.env['res.partner'].browse(self._context.get('active_ids')[:1]).omiid)

    def action_confirm(self):
        print ('action_confirm')
        active_ids = self._context.get('active_id') and [self._context.get('active_id')] or self._context.get('active_ids')
        active_ids = safe_eval(self.active_ids)
        action = self.env.ref('dc_crm1.omicall_wizard_action').sudo().read()[0]
        action['res_id'] = self.id
        if self.active_model != 'res.partner':
            active_ids = []
        partners = self.env['res.partner'].browse(active_ids)
        if self.active_model == 'res.partner':
            if not partners:
                self.message = 'không tồn tại partner'
                return action
        # partner = partners[0]
        messages = []
        _logger.info('type %s'%self.type_id.code)
        partner = partners
        if self.active_model != 'res.partner':
            partners = [partners]
        
        for partner in partners:
            if self.type_id.code == 'omi_get':
                message = partner.omi_get(self.phone)
            elif self.type_id.code == 'omi_get_by_omiid':
                message = partner.omi_get_by_omiid(self.omiid)
            elif self.type_id.code == 'get_call_transaction_list':
                message = partner.get_call_transaction_list(self.from_date, self.to_date)
            elif self.type_id.code == 'create_call_history':
                message = partner.create_call_history(self.from_date, self.to_date)
            else:
                message = getattr(partner, self.type_id.code)()
            
            self.status_code = message and isinstance(message, dict) and message.get('res') and message.get('res').get('status_code')
            messages.append(message)
            if self.type_id.code not in ('omi_create', 'omi_edit', 'omi_delete','omi_get', 'omi_get_by_omiid'):
                break
        self.message = '\n'.join([i and str(i) or '' for i in messages])
        return action

    # def omicall_create_contact(self):

        