# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

   
    is_send_omi = fields.Boolean('is_allow_send_to_omicall', config_parameter='omicall_api.is_send_omi')
    # is_allow_send_to_omicall2 = fields.Char('is_allow_send_to_omicall', config_parameter='dc_crm1.is_allow_send_to_omicall2')
   