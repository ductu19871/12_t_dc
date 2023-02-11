# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from datetime import datetime, date
from odoo.tools.misc import formatLang, format_date
import logging
from odoo import SUPERUSER_ID
_logger = logging.getLogger(__name__)



####################LS xúc tiến############
class CL(models.Model):
    _name = 'crm.connection'
    _description = 'Lịch sử xúc tiến'

    name = fields.Text(string='Nội dung')
    date = fields.Date(default=fields.Date.context_today)
    crm_id = fields.Many2one('crm.lead', ondelete='cascade')
    # parent_crm_id = fields.Many2one('crm.lead', ondelete='cascade')
    parent_crm_id = fields.Many2one('crm.lead', ondelete='cascade', compute='_compute_parent_crm_id', store=True, readonly=False)
    
    @api.depends('crm_id')
    def _compute_parent_crm_id(self):
        for r in self:
            r.partner_parent_id= r.crm_id.order_id

