# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
from datetime import timedelta
from odoo.addons import decimal_precision as dp


class CreadSOWizard(models.TransientModel):
    _name = "pre.create.so.wizard"
    _description = "create.so.wizard"

    crm_id = fields.Many2one('crm.lead', string='CRM', readonly=True, required=True)
    qty_remain_fname = fields.Selection([('qty_remain','qty_remain'),('quotation_qty_remain','quotation_qty_remain')],
        default='quotation_qty_remain',
        required=True)
    
    
    @api.model
    def default_get(self, fields):
        res = super(CreadSOWizard, self).default_get(fields)
        crm_id = self._context.get('active_id') or False
        res.update({
            'crm_id': crm_id,
        })
        return res

    def action_confirm(self):
        # next_create_so_wizard = self.env['create.so.wizard']
        action = self.env.ref('dc_crm1.create_so_wizard_action').sudo().read()[0]
        action['res_id'] = self.crm_id._create_default_create_so_wizard(self.qty_remain_fname)
        return action