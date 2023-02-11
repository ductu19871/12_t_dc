# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from datetime import datetime, date
from odoo.tools.misc import formatLang, format_date
import logging
from odoo import SUPERUSER_ID
_logger = logging.getLogger(__name__)


class SO(models.Model):
    _inherit = 'sale.order.line'

    crm_product_line_id = fields.Many2one('crm.lead', copy=False)
