from odoo.http import request
from odoo import http
import json
import logging
_logger = logging.getLogger(__name__)
from odoo.http import Response
# from odoo.addons.

###########
        
class TestResponseJson (http.Controller):
    
    @http.route(['''/save_call_history''',
    ], type='json', auth="none", methods=['GET','POST'])
    def save_call_history(self):
        _logger.info('..............save_call_history..............save_call_history')
        data = request.jsonrequest or {}
        _logger.info(data)
        _logger.info(type(data))
        if 'transaction_id' in data or 1:
            request.env['omicall.history'].with_context(prevent_send_api_omi=1).sudo().create_one_call_history(data)
        else:
            obj = request.env['ndt.10'].sudo()
            obj.create({'a1':1, 'a2':json.dumps(data or {}) })
        rs = {'res':'that ok'}
        mime = 'application/json'
        return Response(
            rs, status=200,
            headers=[('Content-Type', mime), ('Content-Length', len(rs))]
        )


    @http.route(['''/omi_contact_webhook''',
    ], type='json', auth="none", methods=['GET','POST'])
    def omi_contact_webhook(self):
        _logger.info('..............omi_contact_webhook.............')
        data = request.jsonrequest or {}
        _logger.info(data)
        _logger.info(type(data))
        # if 'transaction_id' in data:
        res = request.env['omicall.history'].with_context(prevent_send_api_omi=1).sudo().webhook_create_contact(data)
        request.env['ndt.10'].sudo().create({'a1':1, 'a2':json.dumps(data or {}) })
        _logger.info(res)
        rs = {'res':'that ok'}
        mime = 'application/json'
        return Response(
            rs, status=200,
            headers=[('Content-Type', mime), ('Content-Length', len(rs))]
        )



