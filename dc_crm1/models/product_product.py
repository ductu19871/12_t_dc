# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from datetime import datetime, date
from odoo.tools.misc import formatLang, format_date
import logging
from odoo import SUPERUSER_ID
_logger = logging.getLogger(__name__)
class PC(models.Model):
    _inherit = 'product.product'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        context = self._context or {}

        if context.get('dc_search_exclude_child_of'):
            for i in args:
                if i[1] == 'child_of' and i[2] == False:
                    args.remove(i)
            # if context.get('type') in ('out_invoice', 'out_refund'):
            #     args += [('type_tax_use', '=', 'sale')]
            # elif context.get('type') in ('in_invoice', 'in_refund'):
            #     args += [('type_tax_use', '=', 'purchase')]
        return super(PC, self)._search(args, offset, limit, order, count=count, access_rights_uid=access_rights_uid)
