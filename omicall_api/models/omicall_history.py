from odoo import fields, models, api
import base64
import io
import json
from datetime import datetime
import requests
from PIL import Image
from odoo.http import request
from datetime import datetime, date
import datetime
from datetime import datetime, timedelta, MINYEAR, date
from datetime import timedelta
from odoo.addons.base.models.ir_ui_view import keep_query
import re
import logging
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

def save_log(self, func_name, partner, ret):
    api_ret = ret.get('ret')#
    if api_ret == 'skip_log':
        return ret
    if partner.type == 'phone':
        partner = partner.parent_id
    if isinstance(ret, dict) and ret.get('send_payload'):# == 'is_save_log_payload':
        send_payload = ret.get('send_payload')
    else:
        send_payload = False
    
    self.env['omi.log'].create({'res_id':partner.id, 
        'model':'res.partner',
        'msg':api_ret,
        'name': func_name, 
        'send_payload': send_payload,
        'mobile_vals': ret.get('mobile_vals'),
        'isdisjoint': ret.get('isdisjoint'),
        'api_ret':api_ret,
        'status_code': isinstance(api_ret,dict) and api_ret.get('status_code'),
        'omiid':ret.get('omiid')
        })
    ret2 =  ret.get('ret2')
    if ret2:
        func_name = ret2['func_name']
        save_log(self, func_name, partner, ret2)
    return ret


def decor_omi_log(func):
    def wrap(self,*args,**kwargs):
        ret = func(self, *args, **kwargs)
        # send_payload = False
        func_name = kwargs.get('func_name') or ret.get('func_name') or func.__name__ 
        # if isinstance(ret, dict) and ret.get('type') == 'is_save_log_payload':
        #     send_payload = ret.get('send_payload')
        # msg = ret.get('ret')
        # self.env['omi.log'].create({'res_id':self.id, 'model':'res.partner',
        #     'msg':msg,
        #     'name': func_name, 
        #     'send_payload': send_payload,
        #     'mobile_vals': ret.get('mobile_vals'),
        #     'isdisjoint': ret.get('isdisjoint')
        #     })
        partner = args[0]
        save_log(self,func_name,partner, ret)
        return ret

    return wrap

class OL(models.Model):
    _name = 'omi.log'
    _order = 'id desc'

    msg = fields.Text()
    send_payload = fields.Text()
    api_ret = fields.Text()
    res_id = fields.Integer()
    model = fields.Char()
    name = fields.Char()
    omiid = fields.Char()
    mobile_vals = fields.Char()
    isdisjoint = fields.Boolean()
    status_code = fields.Char()

class ApiWine(models.Model):
    _name = "omicall.history"
    # _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    url_id = fields.Many2one('wine.api.url', string='Đường dẫn')
    create_date = fields.Datetime('Thòi gian tạo')
    create_date_p = fields.Datetime('Thời gian gọi')
    record_seconds = fields.Integer('Thời lượng cuộc gọi')
    # user_id = fields.Many2one('res.users')
    transaction_id = fields.Char('ID cuộc gọi')
    direction = fields.Char('Trạng thái')
    hotline = fields.Char('Hotline')
    destination_number = fields.Char('Số khách hàng')
    disposition = fields.Char('Tình trạng cuộc gọi')
    recording_file = fields.Char('File ghi âm')
    customer_name = fields.Char('Khách hàng (OMI)')
    user_name = fields.Char('Nhân viên')
    tag_name = fields.Char('Tag')
    json_request = fields.Char('Json Request')
    call_out_price = fields.Float('Cước phí')
    provider = fields.Char('Nhà mạng')
    crm_id = fields.Many2one('crm.lead', string='Cơ hội')
    partner_ids = fields.Many2many('res.partner', compute='_compute_partner_ids', string='Khách hàng (ERP)')
    dc_crm_ids = fields.Many2many('crm.lead', compute='_compute_partner_ids',  string='Tiềm năng')
    len_dc_crm_ids = fields.Integer(compute='_compute_partner_ids', string='Số lượng cơ hội')
    sale_order_ids = fields.Many2many('sale.order', compute='_compute_partner_ids', string='Đơn đặt hàng')
    len_sale_order_ids = fields.Integer(compute='_compute_partner_ids', string='SL Đơn đặt hàng')
    
    def get_omicall_token(self):
        company_id = self.env['res.company'].browse(1)
        kw = {'apiKey': company_id.api_key}
        url = 'https://public-v1-stg.omicall.com/api/auth?' + keep_query('*', **kw)
        method = 'get'
        rs = self.omi_api_common(url, method=method)
        try:
            omi_token = rs['payload']['access_token']
            print ('**omi_token**', omi_token)
            company_id.omi_token = omi_token
            return omi_token
        except:
            return rs
    
    def omi_api_common(self, url, vals={}, method='post'):
        IS_RAISE = self._context.get('is_authen_omi_raise')
        # url = 'https://public-v1-stg.omicall.com/api/contacts/update'
        print ('url',url )
        company_id = self.env['res.company'].browse(1)
        token = ''
        if company_id.omi_token:#
            token = 'Bearer' + ' ' + company_id.omi_token
        else:
            raise UserError('omi_token cant not empty')
        data = json.dumps(vals)
        func = getattr(requests, method)
        list_request = func(url=url, data=data,
                                     headers={"Content-type": "application/json", "Authorization": token})
        try:
            response = json.loads(list_request.content)
        except:
            response = list_request.content.decode('utf-8')
        
        if not isinstance(response, dict):
            if IS_RAISE :
                raise UserError('lỗi authen :%s'%response)
            else:
                return {'ret':'lỗi authen :%s'%response}
        return response

    def re_phone(self, val):
        return re.sub('\s*ext.*','',val)

    def add_phone_mobiles(self, partners):
        data_phone=[]
        data_mail=[]
        for partner in partners:
            if partner.phone:
                data_phone.append({
                        "data": self.re_phone(partner.phone),
                        "type": "office",
                        "valueType": "Công ty"
                    })
            if partner.mobile:
                data_phone.append({
                        "data": self.re_phone(partner.mobile),
                        "type": "personal",
                        "valueType": "Cá nhân"
                    })
            if partner.mobile2:
                data_phone.append({
                        "data": self.re_phone(partner.mobile2),
                        "type": "personal",
                        "valueType": "Cá nhân"
                    })
            if partner.mobile3:
                data_phone.append({
                        "data": self.re_phone(partner.mobile3),
                        "type": "personal",
                        "valueType": "Cá nhân"
                    })
                
            if partner.email:
                data_mail.append({
                        "data": partner.email,
                        "type": "office",
                        "valueType": "Công ty"
                    })
        return data_phone, data_mail


    def gen_phone_vals(self, partner, rais_if_not_phone = False):
        result = partner
        other_childs = result.child_ids.filtered(lambda i: i.type =='phone')
        data_phone, data_mail = self.add_phone_mobiles(result | other_childs)
        if rais_if_not_phone and not data_phone:
            raise UserError('User not has any phone')
        return data_phone, data_mail
    
    def gen_phone_vals_only(self, partner, rais_if_not_phone = False):
        data_phone, data_mail = self.gen_phone_vals(partner)
        data_phone_only = [i['data'] for i in data_phone]
        return data_phone_only
    
    def gen_omi_edit_data(self, partner):
        result = partner
        # data_phone = []
        # data_mail = []
        vals = {
            "refid": result['id'],
            "user_owner_email": 'it@dctech.com.vn',#self.env['res.users'].browse(2).account_omi,
            "refcode": str(result['id']
            ),
            "fullName": result['name'],
            "note": result.sale_summary or 'Chưa có đơn hàng',
            # "phones": data_phone,
            # "emails": data_mail
        }
        data_phone, data_mail= self.gen_phone_vals(result)
        if not data_phone:
            raise ValueError('not omicall data_phone')
        vals['phones'] = data_phone
        vals['emails'] = data_mail
        # other_childs = result.child_ids.filtered(lambda i: i.type =='phone')
        # self.add_phone_mobiles(result | other_childs)
        # self.add_phone_mobiles(other_childs, data_phone=data_phone, data_mail=data_mail)
        return vals  

    # @decor_omi_log
    def omi_create(self, partner, is_update_token=True):
        return self.omi_edit(partner,is_update_token=is_update_token, isdisjoint=True, func_name='omi_create', create_url = 'https://public-v1-stg.omicall.com/api/contacts/add')

    def omi_edits(self, partners, is_update_token=True, isdisjoint=None, func_name=None, create_url=None, vals={}, obj_dict_list=[], fields_vals={}):
        for count, partner in enumerate(partners):
            obj_dict = obj_dict_list[count]
            self.omi_edit(partner, vals=vals,obj_dict=obj_dict,fields_vals=fields_vals)

    
    @decor_omi_log
    def omi_edit(self, partner, is_update_token=True, isdisjoint=None, func_name=None, create_url=None, vals={}, obj_dict={},fields_vals={}):
        # if self._context.get('prevent_send_api_omi'):
        #     return {'res':'prevent_send_api_omi'}
        if obj_dict and fields_vals and obj_dict==fields_vals:
            return {'ret': 'no_change'}
        if partner.type not in ('contact','phone'):
            return {'ret': 'skip_log'}
            raise UserError('partner.type must be contact or phone')
        if partner.type =='phone':
            if not set(vals).isdisjoint({ 'phone','mobile'}):
                return {'ret': 'skip_log'}
            partner= partner.parent_id
            if not partner:
                raise UserError('partner.type phone but not has parent')
        try:
            vals = self.gen_omi_edit_data(partner)
        except ValueError as e:
            return {'ret':str(e)}

        url = create_url or 'https://public-v1-stg.omicall.com/api/contacts/update'
        vals['url'] = url
        api_ret = self.omi_api_common(url, vals, 'post')
        ret2 = None
        if is_update_token and api_ret.get('status_code')==9999:
            ret2 = self.update_omiid_no_log(partner)
            ret2['func_name'] = 'update_omiid'
        return {'ret':api_ret, 'ret2':ret2, 'send_payload':vals,  'mobile_vals':vals['phones'], 'isdisjoint': isdisjoint}

    def omi_list(self):
        vals = {'page':1, 'size':500}#, 'keyword':'78'
        # vals['keyword'] = '09100000'#ăn nhưng nó giống như get
        # vals['filters'] = [ 
        #                 { 
        #                 "field_code" : "phone_number", #// Người phụ trách
        #                     "value":[
        #                         # "unassigned",  #// chưa gán 
        #                         self.phone#// Email nhân nhân viên 
        #                         # self.mobile
        #                     ] 
        #                 } ]
        url = 'https://public-v1-stg.omicall.com/api/contacts/list'
        rs = self.omi_api_common(url, vals, 'post')
        return {'res': rs, 'send_payload':vals}

    def omi_get(self, partner,  phone=None):
        phones, emails = self.gen_phone_vals(partner, True)
        # phones = ', '.join([i for i in [self.phone, self.mobile] if i])
        # if not phone:
        #     phone = partner.phone or partner.mobile
        if phones:
            phone = phones[0]['data']
        kw = {'phone': phone}
        url = 'https://public-v1-stg.omicall.com/api/contacts/get?' + keep_query('*', **kw)
        rs = self.omi_api_common(url, {}, 'get')
        rs['send_payload'] = url
        return rs

    @decor_omi_log
    def update_omiid(self, partner):
        return self.update_omiid_no_log(partner)

    def update_omiid_no_log(self, partner):
        api_ret = self.omi_get(partner)
        payload = api_ret['payload']
        omiid = payload and payload['_id'] or False
        if omiid:
            partner.omiid = omiid
            partner.env['omi.log'].search([('name','in',['omi_create', 'omi_edit']),('omiid','=',False)]).write({'omiid':omiid})
        return {'ret': api_ret, 'send_payload':api_ret['send_payload'], 'omiid': omiid}

    def omi_get_by_omiid(self, partner, omiid=None):
        omiid = omiid or partner.omiid
        url = 'https://public-v1-stg.omicall.com/api/contacts/details/%s'%omiid
        rs = self.omi_api_common(url, {}, 'get')
        return {'res':rs}


    def omi_delete(self, partner):
        url = 'https://public-v1-stg.omicall.com/api/contacts/delete/%s'%partner.omiid
        msg = self.omi_api_common(url,{}, 'delete')
        return msg

    def omi_get_webhook(self):
        url = 'https://public-v1-stg.omicall.com/api/webhooks/list'
        rs = self.omi_api_common(url, {}, 'get')
        return rs

    def destroy_contact_webhook(self):
        url = 'https://public-v1-stg.omicall.com/api/webhooks/destroy?hook_type=contact'
        rs = self.omi_api_common(url, {}, 'post')
        return rs

    def destroy_call_webhook(self):
        url = 'https://public-v1-stg.omicall.com/api/webhooks/destroy?hook_type=call'
        rs = self.omi_api_common(url, {}, 'post')
        return rs
    
    def add_contact_webhook(self):
        self.destroy_contact_webhook()
        url = 'https://public-v1-stg.omicall.com/api/webhooks/register'
        vals  = { 
            "webhook" : { 
            "type" : "contact", 
                # "url" : "http://14.225.254.216:8069/test_respone_json" ,
                "url" : "http://69.197.140.91:8069/omi_contact_webhook" ,
                "events": [
                            "ringing",
                            "answered",
                            "hangup"
                        ]
            } 
        }
        rs = self.omi_api_common(url, vals, 'post')
        return rs

    def add_call_webhook(self):
        self.destroy_call_webhook()
        url = 'https://public-v1-stg.omicall.com/api/webhooks/register'
        vals  = { 
            "webhook" : { 
            "type" : "call", 
                "url" : "http://69.197.140.91:8069/save_call_history" ,
                "events": [
                            # "ringing",
                            # "answered",
                            "hangup"
                        ]
            } 
        }
        rs = self.omi_api_common(url, vals, 'post')
        return rs

    def get_call_transaction_list(self, from_time=None, to_time=None):
        now = date.today()
        date_time_1 = now.strftime('%d/%m/%Y 00:00:01')
        date_time_3 = now.strftime('%d/%m/%Y 23:59:59')
        date_time_2 = datetime.strptime(date_time_1, '%d/%m/%Y %H:%M:%S')
        date_time_4 = datetime.strptime (date_time_3, '%d/%m/%Y %H:%M:%S')

        
        if not from_time:
            from_time = date_time_2
        if not to_time:
            to_time = date_time_4
        if isinstance(from_time, date):
            str_from_time = str(from_time) + ' 00:00:00'
            from_time = datetime.strptime(str_from_time, '%Y-%m-%d %H:%M:%S')
        if isinstance(to_time, date):
            to_time = str(to_time) + ' 23:59:59'
            to_time = datetime.strptime(to_time, '%Y-%m-%d %H:%M:%S')
            print (to_time)
        ts1 = int(from_time.timestamp() * 1000)
        ts2 = int (to_time.timestamp() * 1000)
        url = "https://public-v1-stg.omicall.com/api/call_transaction/list?"
        from_date = 'from_date='+str(ts1)
        v = '&'
        to_date = 'to_date='+str(ts2)
        url_getdata = url+from_date+v+to_date
        company_id = self.env['res.company'].browse(1)
        token = ''
        if company_id:
            if company_id.omi_token:
                token = 'Bearer' + ' ' + company_id.omi_token
        list_request = requests.get(url=url_getdata, data={},
                                                  headers={"Content-type": "application/json", "Authorization": token})
        try:
            response = json.loads(list_request.content)
        except:
            response = list_request.content.decode('utf-8')
        return response

    def create_one_call_history(self, list_transaction):
        timestamp = str(list_transaction.get('created_date') or list_transaction['created_time'])
        time = timestamp[0:10]
        create_day = int(time)
        date_time = datetime.fromtimestamp(create_day)
        str_date_time = date_time.strftime("%Y-%m-%d %H:%M:%S")
        hotline = list_transaction['hotline']
        direction = list_transaction['direction']

        if 'transaction_id' not in list_transaction:
            if direction in ('inbound',):#outbound, local
                customer_number = list_transaction['from_number']
            else:
                customer_number = list_transaction['to_number']
        else:
            if direction in ('inbound',):#outbound, local
                customer_number = list_transaction['phone_number']#phone_number list_transaction['source_number']
            elif direction in ('outbound',):
                customer_number = list_transaction['phone_number']#phone_number list_transaction['to_number']
            else:
                customer_number = list_transaction['destination_number']
        if customer_number[0] != '0':
            customer_number = '0' + customer_number
        data = {
            'hotline':hotline,
            'destination_number': customer_number,
            'json_request': list_transaction,
            'direction': direction,
            'hotline': hotline,
            'create_date_p':str_date_time
        }
        if 'transaction_id' not in list_transaction:
            disposition = list_transaction['state']
        else:
            disposition = list_transaction['disposition']
        data['disposition'] = disposition
        if 'transaction_id' not in list_transaction:
            item = self.env['omicall.history'].create(data)
            return item
        else:
            customer_name = False
            if list_transaction.get('customer'):
                customer_name = list_transaction['customer']['full_name']
            transaction_id = list_transaction['transaction_id']
            data_update = {
                'transaction_id': transaction_id,
                'record_seconds': list_transaction['record_seconds'],
                'provider': list_transaction['provider'],
                'user_name': list_transaction['user'][0]['full_name'],
                'customer_name': customer_name,
                'recording_file': list_transaction.get('recording_file'),
                'call_out_price': list_transaction.get('call_out_price'),
                'tag_name': list_transaction['user'][0].get('tag'),
                }
            data.update(data_update)
            item = False
            if not self.env['omicall.history'].search([('transaction_id','=', transaction_id)]):
                item = self.env['omicall.history'].create(data)
            return item
    
    def create_call_history(self, from_time=None, to_time=None):
        response = self.get_call_transaction_list(from_time, to_time)
        list_email = []
        if response.get('payload'):
            payload = response.get('payload')
            if payload.get('items'):
                direction_adds = []
                for list_transaction in payload.get('items'):
                    item  = self.create_one_call_history(list_transaction)
                    if item:
                        direction_adds.append( list_transaction['destination_number'])
        return {'res':response,'direction_adds':direction_adds }


    def webhook_create_contact(self, vals=None):
        vals_mau =  {
            "action": "created",
            "data": [{
                "is_active": False,
                "is_member": False,
                "attribute_structure": [{
                    "identify": False,
                    "attribute_id": "63b451a3285ac55c618f1aea",
                    "field_code": "avatar",
                    "field_type": "image",
                    "value": [{
                        "display_value": "",
                        "value_type": "",
                        "data_type": "",
                        "value_id": "63b451a3285ac55c618f1aeb"
                    }]
                }, {
                    "identify": False,
                    "attribute_id": "63b451a3285ac55c618f1aec",
                    "field_code": "gender",
                    "field_type": "radio",
                    "value": [{
                        "display_value": "male",
                        "value_type": "",
                        "data_type": "",
                        "value_id": "63b451a3285ac55c618f1aed"
                    }]
                }, {
                    "identify": False,
                    "attribute_id": "63b451a3285ac55c618f1aee",
                    "field_code": "full_name",
                    "field_type": "single_text",
                    "value": [{
                        "display_value": "KH PV (s\u1eeda)",
                        "value_type": "",
                        "data_type": "",
                        "value_id": "63b451a3285ac55c618f1aef"
                    }]
                }, {
                    "identify": False,
                    "attribute_id": "63b451a3285ac55c618f1af0",
                    "field_code": "phone_number",
                    "field_type": "phone",
                    "value": [{
                        "display_value": "0367085685",
                        "value_type": "C\u00e1 nh\u00e2n",
                        "data_type": "personal",
                        "value_id": "63b451a3285ac55c618f1af1"
                    }, {
                        "display_value": "0367085684",
                        "value_type": "C\u00e1 nh\u00e2n",
                        "data_type": "personal",
                        "value_id": "63b451a3285ac55c618f1af2"
                    }]
                }, {
                    "identify": False,
                    "attribute_id": "63b451a3285ac55c618f1af3",
                    "field_code": "mail",
                    "field_type": "email",
                    "value": []
                }, {
                    "identify": False,
                    "attribute_id": "63b451a3285ac55c618f1af4",
                    "field_code": "birthday",
                    "field_type": "date",
                    "value": [{
                        "display_value": "",
                        "value_type": "",
                        "data_type": "",
                        "value_id": "63b451a3285ac55c618f1af5"
                    }]
                }, {
                    "identify": False,
                    "attribute_id": "63b451a3285ac55c618f1af6",
                    "field_code": "attach_file",
                    "field_type": "file",
                    "value": []
                }, {
                    "identify": False,
                    "attribute_id": "63b451a3285ac55c618f1af7",
                    "field_code": "ref_id",
                    "field_type": "single_text",
                    "value": [{
                        "display_value": "",
                        "value_type": "",
                        "data_type": "",
                        "value_id": "63b451a3285ac55c618f1af8"
                    }]
                }, {
                    "identify": False,
                    "attribute_id": "63b451a3285ac55c618f1af9",
                    "field_code": "job_title",
                    "field_type": "single_text",
                    "value": [{
                        "display_value": "",
                        "value_type": "",
                        "data_type": "",
                        "value_id": "63b451a3285ac55c618f1afa"
                    }]
                }, {
                    "identify": False,
                    "attribute_id": "63b451a3285ac55c618f1afb",
                    "field_code": "passport",
                    "field_type": "single_text",
                    "value": [{
                        "display_value": "",
                        "value_type": "",
                        "data_type": "",
                        "value_id": "63b451a3285ac55c618f1afc"
                    }]
                }, {
                    "identify": False,
                    "attribute_id": "63b451a3285ac55c618f1afd",
                    "field_code": "address",
                    "field_type": "single_text",
                    "value": [{
                        "display_value": "",
                        "value_type": "",
                        "data_type": "",
                        "value_id": "63b451a3285ac55c618f1afe"
                    }]
                }, {
                    "identify": False,
                    "attribute_id": "63b451a3285ac55c618f1aff",
                    "field_code": "more_infomation",
                    "field_type": "customize",
                    "value": [{
                        "display_value": "",
                        "value_type": "",
                        "data_type": "",
                        "value_id": "63b451a3285ac55c618f1b00"
                    }]
                }, {
                    "identify": False,
                    "attribute_id": "63b451a3285ac55c618f1b01",
                    "field_code": "note",
                    "field_type": "multi_text",
                    "value": [{
                        "display_value": "",
                        "value_type": "",
                        "data_type": "",
                        "value_id": "63b451a3285ac55c618f1b02"
                    }]
                }],
                "contact_id": "63b44e47a2523f37e3709c59",
                "user_owner_email": "it@dctech.com.vn",
                "tags": [],
                "create_by": {
                    "name": "P.Cung \u1ee8ng",
                    "id": "6348daf0662a784a01660927"
                },
                "contact_type": "contact",
                "last_update_by": {
                    "name": "P.Cung \u1ee8ng",
                    "id": "6348daf0662a784a01660927"
                },
                "is_deleted": False,
                "business_type": [],
                "source_add": [],
                "created_date": 1672760903265,
                "last_updated_date": 1672761763435,
                "user_owner_id": "6348daf35434a97a92dd8f96",
                "contact_categories": []
            }],
            "tenant_id": "6348daf0662a784a01660924"
        }
        vals = vals or vals_mau
        res = 'NO contact duoc tao'
        name,mobile, phone, omiid = self.gen_partner_data_webhook(vals)
        if name and  omiid and vals.get('action') in ('updated', 'created', 'create'):
            phone_mobile = [i for i in (phone,mobile) if i]
            partner = self.env['res.partner'].search(['|','|',('phone','in',phone_mobile), ('mobile','in',phone_mobile),('omiid','=',omiid)], order='id desc', limit=1)
            # if vals.get('action') == 'updated':
            #     # partner = self.env['res.partner'].search([('omiid','=',omiid)])
            #     if partner:
            #         partner.write({'name':name, 'mobile':mobile, 'phone':phone, 'omiid':omiid})
            #         res =  {'res': {'name':name, 'mobile':mobile, 'phone':phone, 'omiid':omiid}, 'partner': partner, 'is_new':False}
            #         return res
            #     else:
            #         res =  {'res': {'name':name, 'mobile':mobile, 'phone':phone, 'omiid':omiid}, 'partner': partner, 'mess':'No exist omiid in odoo'}

            # if vals.get('action') == 'created':
            if partner:
                partner.write({'name':name, 'mobile':mobile, 'phone':phone, 'omiid':omiid})
                res =  {'res': {'name':name, 'mobile':mobile, 'phone':phone, 'omiid':omiid}, 'partner': partner, 'is_new':False}
                return res
            else:
                partner = self.env['res.partner'].create({'name':name, 'mobile':mobile, 'phone':phone, 'omiid':omiid})
                return {'res': {'name':name, 'mobile':mobile, 'phone':phone, 'omiid':omiid}, 'partner': partner, 'is_new':True}
        else:
            return {'res': 'No  omiid in webhook data '}

    def gen_partner_data_webhook(self, vals):
        data = vals.get('data') and vals.get('data')[0]
        # new_partner = False
        name,mobile,phone, omiid = False,False,False, False
        if data:
            omiid = data.get('contact_id')
            attribute_structure = data.get('attribute_structure')
            name,mobile,phone = False,False,False
            _logger.info(data)
            for i in attribute_structure[::-1]:#dau xanh sao loi 
                if i['field_code'] == 'full_name':
                    name = i['value'][0]['display_value']
                elif i['field_code'] == 'phone_number':
                    values = i['value']
                    for number_dict in values:
                        if number_dict['data_type'] == 'personal':
                            mobile = number_dict['display_value']
                        elif number_dict['data_type'] in ('home','office'):
                            phone = number_dict['display_value']
        return name,mobile,phone, omiid




    def open_crm(self):
        action = self.env.ref('crm.crm_lead_opportunities_tree_view').sudo().read()[0]
        # action['view_mode'] = 'form'
        # action['view_type'] = 'form'
        action['target'] = 'current'
        # action['res_id'] = self.crm_id.id 
        # del action['id']
        # action['views'] = [
        #             (self.env.ref('crm.crm_case_form_view_oppor').id, 'form')
        #         ]
        action['domain'] = [('id','=', self.dc_crm_ids.ids)]
        print (action)
        return action

    def open_crm(self):

        return {
                'type': 'ir.actions.act_url',
                'url': 'http://localhost:8069/web?debug=1#id=71&action=153&model=crm.lead&view_type=form&menu_id=111',
                'target': 'new',
                'target_type': 'public',
                'res_id': self.dc_crm_ids[:1].id,
            }

        action = self.env.ref('crm.crm_lead_opportunities_tree_view').sudo().read()[0]
        action['view_mode'] = 'form'
        action['target'] = 'current'
        action['res_id'] = self.dc_crm_ids[:1].id
        # del action['id']
        # action['views'] = [
        #             (self.env.ref('crm.crm_case_form_view_oppor').id, 'form')
        #         ]
        # action['domain'] = [('id','=', self.dc_crm_ids[:1].id)]
        del action['domain']
        del action['id']
        action['views'] =  [
                    (self.env.ref('crm.crm_case_form_view_oppor').id, 'form'),
                ]
        print (action)
        return action

    def open_crm1(self):
        views = [
                    (self.env.ref('crm.crm_case_form_view_oppor').id, 'form'),
                ]
        action = {
                'type': 'ir.actions.act_window',
                'views':views ,
                'view_mode': 'form',
                'name': 'CRM',
                'res_model': 'crm.lead',
                'res_id':self.dc_crm_ids[:1].id,
                'target':'current'
            }
        return action

    def open_crm_new(self,target='new'):
        views = [
                    (self.env.ref('crm.crm_case_form_view_oppor').id, 'form'),
                ]
        action = {
                'type': 'ir.actions.act_window',
                'views':views ,
                'view_mode': 'form',
                'name': 'CRM',
                'res_model': 'crm.lead',
                'res_id':self.dc_crm_ids[:1].id,
                'target':target
            }
        return action

    def open_crm_current(self):
        return self.open_crm_new('current')

    def open_crm_inline(self):
        return self.open_crm_new('inline')

    def open_crm_fullscreen(self):
        return self.open_crm_new('fullscreen')

    def open_crm_main(self):
        return self.open_crm_new('main')

    def _compute_partner_ids(self):
        operator = 'ilike'
        for r in self:
            # partner_ids = self.env['res.partner']
            partner_ids = self.env['res.partner'].search([('type','!=','phone'),'|', ('phone', operator, r.destination_number), ('mobile',operator,r.destination_number)])
            child_ids = self.env['res.partner'].search([('type','=','phone'),'|', ('phone',operator,r.destination_number), ('mobile',operator, r.destination_number)])
            r.partner_ids = partner_ids | child_ids.mapped('parent_id')
            r.dc_crm_ids = partner_ids.mapped('dc_crm_ids')
            r.len_dc_crm_ids = len(r.dc_crm_ids)
            r.sale_order_ids = r.partner_ids.mapped('sale_order_ids')
            r.len_sale_order_ids = len(r.sale_order_ids)
    
    def name_get(self):
        result = [] 
        for rec in self:
            result.append((rec.id, '%s/ %s' % ("Omi",rec.id)))
        return result
    
    # @api.model
    # def get_token(self):
    #     print ('get token')
    #     company_id = self.env['res.company'].browse(1)
    #     if company_id:
    #         url = self.env.ref('wine_api.url_get_token').url + company_id.api_key
    #         response = requests.get(url)
    #         ls_json = response.json()
    #         omi_token = ls_json['payload']['access_token']
    #         print ('**omi_token**', omi_token)
    #         company_id.omi_token = omi_token

    def get_data_everyday(self):
        pass
        