# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class CS(models.Model):
    _inherit = 'crm.stage'

    active = fields.Boolean()