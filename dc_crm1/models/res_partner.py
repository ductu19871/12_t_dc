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
    _inherit = 'res.partner'

    mobile2 = fields.Char('Di động 2')
    mobile3 = fields.Char('Di động 3')
    facebook = fields.Char()
    Linkedin = fields.Char()
    is_control = fields.Boolean() 
    hobby = fields.Char('Sở thích')
    # birthdate = fields.Date()
    