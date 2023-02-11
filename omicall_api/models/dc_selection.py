# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
# from odoo.addons import decimal_precision as dp
# from datetime import datetime, date


class DCselection(models.Model):
    _name = 'dc.selection'

    _sql_constraints = [
        ('code_uniq', 'unique (code,model)', 'code must be unique !'),
        ('name_uniq', 'unique (name,model)', 'name must be unique !')
        ]

    code = fields.Char()
    name = fields.Char()
    model = fields.Char()
    type = fields.Char()