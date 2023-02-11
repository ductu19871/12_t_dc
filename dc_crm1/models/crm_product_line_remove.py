# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from datetime import datetime, date
from odoo.tools.misc import formatLang, format_date
import logging
from odoo import SUPERUSER_ID
_logger = logging.getLogger(__name__)
class CRMProductLine(models.Model):
    _name = 'crm.lead'
    _inherit = ['crm.lead']

    _sql_constraints = [
        ('crm_line_uniq', 'unique (order_id, product_id, select_categ_id)', 'order_id, product_id,select_categ_id must be unique !')]
    
    order_line_ids = fields.One2many('sale.order.line', 'crm_product_line_id' )
    qty_done = fields.Float(compute='_compute_qty_done', string='Số lượng đã tạo đơn hàng', store=True, 
        digits=dp.get_precision('Product Unit of Measure'))
    qty_remain = fields.Float(compute='_compute_qty_remain', store=True, digits=dp.get_precision('Product Unit of Measure'))
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency", readonly=True, store=True, compute_sudo=True)
    so_price_total = fields.Float(compute='_compute_so_price_total', store=True, string='Đã tạo đơn hàng')
    so_price_unit = fields.Float(compute='_compute_so_price_total', store=True, string='Đơn giá ở đơn hàng')
    select_categ_id  = fields.Many2one('product.category', string='Chọn Nhóm SP')
    # partner_id = fields.Many2one('res.partner', related='order_id.partner_id')
    
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        # retrieve team_id from the context and write the domain
        # - ('id', 'in', stages.ids): add columns that should be present
        # - OR ('fold', '=', False): add default columns that are not folded
        # - OR ('team_ids', '=', team_id), ('fold', '=', False) if team_id: add team columns that are not folded
        team_id = self._context.get('default_team_id')
        if team_id:
            search_domain = ['|', ('id', 'in', stages.ids), '|', ('team_id', '=', False), ('team_id', '=', team_id)]
        else:
            search_domain = ['|', ('id', 'in', stages.ids), ('team_id', '=', False)]

        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.depends('order_line.so_price_total','order_line_ids.state', 'order_line_ids.price_total')
    def _compute_so_price_total(self):
        for r in self:
            if not r.order_line:
                order_line_ids = r.order_line_ids.filtered(lambda i: i.state in ('sale','done'))
                r.so_price_total = order_line_ids and sum(order_line_ids.mapped('price_total'))
                r.so_price_unit = order_line_ids and sum(order_line_ids.mapped('price_unit'))/len(order_line_ids)
            else:
                r.so_price_total  = sum(r.order_line.mapped('so_price_total'))
    #  def _compute_quantity(self, qty, to_unit, round=True, rounding_method='UP', raise_if_failure=True):
    @api.depends('order_line.qty_done','order_line_ids.state','order_line_ids.product_uom_qty','order_line_ids.product_uom','product_uom')
    def _compute_qty_done(self):
        for r in self:
            if not r.order_line:
                order_line_ids = r.order_line_ids.filtered(lambda i: i.state in ('sale','done'))
                qty_done = 0.0
                for l in order_line_ids:
                    qty = l.product_uom._compute_quantity(l.product_uom_qty, r.product_uom)
                    qty_done +=qty
                r.qty_done = qty_done
            else:
                r.qty_done = sum(r.order_line.mapped('qty_done'))

    @api.depends( 'product_uom_qty','qty_done')
    def _compute_qty_remain(self):
        for r in self:
            r.qty_remain = r.product_uom_qty - r.qty_done
    is_win = fields.Boolean(compute='_compute_win_state', store=True)
    so_price_total = fields.Float(compute='_compute_so_price_total', store=True)
    so_price_unit = fields.Float(compute='_compute_so_price_total', store=True)
    select_categ_id  = fields.Many2one('product.category', string='Chọn Nhóm SP')
    