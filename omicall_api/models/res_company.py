
from odoo import fields, models, api
import base64
import io
import json
from datetime import datetime
import requests
from PIL import Image


class ResCompany(models.Model):
    _inherit = 'res.company'

    omi_token = fields.Char('Token')
    api_key = fields.Char('Api key')
