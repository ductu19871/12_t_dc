from odoo import api, fields, models, exceptions, _
from datetime import timedelta
from odoo.tools.misc import format_date




class ReportWizard(models.AbstractModel):
    _name = 'tl.report.wizard.common'
    _description = 'Report Wizard'

    # def init(self):
    #     self.env.cr.execute("""
    #         CREATE OR REPLACE FUNCTION get_qty_conv(qty FLOAT, unit FLOAT)
    #         RETURNS TEXT AS $$
    #         BEGIN
    #             IF unit = 0 THEN return ''; END IF;
    #             return 
    #                 CASE
    #                 WHEN TRUNC((qty / (1 / unit))::numeric, 0) <> 0 AND TRUNC((qty::numeric % (1 / unit)::numeric), 0) = 0
    #                     THEN TRUNC((qty / (1 / unit))::numeric, 0) || ' hộp'
    #                 WHEN TRUNC((qty / (1 / unit))::numeric, 0) = 0 AND TRUNC((qty::numeric % (1 / unit)::numeric), 0) <> 0
    #                     THEN TRUNC((qty::numeric % (1 / unit)::numeric), 0) || ' viên'
    #                 WHEN TRUNC((qty / (1 / unit))::numeric, 0) <> 0 AND TRUNC((qty::numeric % (1 / unit)::numeric), 0) <> 0
    #                     THEN TRUNC((qty / (1 / unit))::numeric, 0) || ' hộp ' || TRUNC((qty::numeric % (1 / unit)::numeric), 0) || ' viên'
    #                 ELSE '' END;
    #         END;
    #         $$  LANGUAGE plpgsql;

    #         CREATE OR REPLACE FUNCTION get_int_conv(qty FLOAT, unit FLOAT)
    #         RETURNS INT AS $$
    #         BEGIN
    #             IF unit = 0 THEN return 0; END IF;
    #             return 
    #                 CASE
    #                 WHEN TRUNC((qty / (1 / unit))::numeric, 0) <> 0
    #                     THEN TRUNC((qty / (1 / unit))::numeric, 0)
    #                 ELSE 0 END;
    #         END;
    #        $$  LANGUAGE plpgsql;

    #         CREATE OR REPLACE FUNCTION get_odd_conv(qty FLOAT, unit FLOAT)
    #         RETURNS INT AS $$
    #         BEGIN
    #             IF unit = 0 THEN return 0; END IF;
    #             return 
    #                 CASE
    #                 WHEN TRUNC((qty::numeric % (1 / unit)::numeric), 0) <> 0
    #                     THEN TRUNC((qty::numeric % (1 / unit)::numeric), 0)
    #                 ELSE 0 END;
    #         END;
    #        $$  LANGUAGE plpgsql;


    #         """
    #     )

    name = fields.Char()
    report = fields.Char()#loại báo cáo
    group_by_ids = fields.Many2many('dc.selection', domain=[('model','=', 'tl.report.wizard')], required=True)

    # name = fields.Char(compute='_compute_name')
    # state = fields.Char(default='confirm')
    # date_from = fields.Date(default=fields.Date.context_today)#Từ ngày
    # date_to = fields.Date(default= lambda self:fields.Date.context_today(self) + timedelta(days=1))#Đến ngày
    # company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)#'Công ty'
    # partner_id = fields.Many2one('res.partner')#Đối tác'
    # categ_id = fields.Many2one('product.category', 'Product Category')#'Nhóm sản phẩm',
    # # partner_type_so = fields.Selection(selection=[('brand', 'Chi nhánh'), ('customer', 'Đại lý, Khách lẻ')], string='Loại đối tác')
    # factory_id = fields.Many2one('res.partner', 
    #     domain="[('type','=','contact'),('supplier','!=',False),'|',('company_id', '=', False),('company_id', '=', company_id)]")#Nhà máy
    # brand_id = fields.Many2one('product.brand')#Nhãn sản phẩm
    # dimension_id = fields.Many2one('product.dimension')#Kích thước
    # product_id = fields.Many2one('product.product')#'Sản phẩm'
    # material_id = fields.Many2one('product.attribute.value', 
    #     domain= lambda self:[('attribute_id','=', self.env.ref('addon_product.product_attribute_material').id)])#'Chất liệu'
    # surface_id = fields.Many2one('product.attribute.value', 
    #     domain= lambda self:[('attribute_id','=', self.env.ref('addon_product.product_attribute_surface').id)])#'Bề mặt'
    # report = fields.Selection([('purchase_report','purchase_report'), ('purchase_detail_report','purchase_detail_report'),
    #     ])#loại báo cáo
    # untaxed_total_currency = fields.Float(compute='_compute_sum')
    # price_total_currency = fields.Float(compute='_compute_sum')
    # qty_ordered = fields.Float(compute='_compute_sum')
    # price_tax_currency = fields.Float(compute='_compute_sum')
    # int_conv = fields.Integer(compute='_compute_sum')
    # odd_conv = fields.Integer(compute='_compute_sum')
    # total_conversion_str = fields.Char(compute='_compute_sum')
    
    # @api.depends('report', 'date_from','date_to')
    # def _compute_name(self):
    #     for r in self:
    #         report_name = self._get_report_mapping_info()[r.report]['report_name']
    #         r.name = '%s %s-%s'%(report_name, format_date(self.env, r.date_from), format_date(self.env,r.date_to))

    # @api.constrains('date_from', 'date_to')
    # def constrains_date(self):
    #     for rec in self:
    #         if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
    #             raise exceptions.ValidationError('Giá trị trường "Đến ngày" không thể nhỏ hơn "Từ ngày"')

    # def name_get(self):
    #     res = []
    #     report_name = self._get_report_mapping_info()[self.report]['report_name']
    #     for record in self:
    #         name = '%s %s-%s'%(report_name, format_date(self.env, self.date_from), format_date(self.env, self.date_to))
    #         res.append((record.id, name))
    #     return res
        
    def _get_report_mapping_info(self):
        rs = {}
        return rs
        rs.update({
            'crm_report':{
                'action_xid':'addon_report.action_tl_report_wizard',
                'model': 'crm.product.line.report',
                'report_list_view_xml_id': 'dc_crm1.action_crm_product_line_report',
                'confirm': 'init_data',
                # 'aeroo_report_xml_id':'addon_purchase_report.action_purchase_report_report_aeroo',
                'report_name': _('BC CRM')
            },
            # 'purchase_detail_report':{
            #     'model': 'purchase.detail.report',
            #     'report_list_view_xml_id': 'addon_purchase_report.action_purchase_detail_report_view',
            #     'aeroo_report_xml_id':'addon_purchase_report.action_purchase_detail_report_report_aeroo',
            #     'report_name': _('Purchase Detail Report')
            # }
        }) 
        return rs

    # def _compute_sum(self):
    #     for r in self:
    #         compute_func = getattr(r, '_compute_sum_%s'%r.report)
    #         if compute_func:
    #             compute_func()

    def action_server_open_tl_report_wizard(self):
        default_report = self._context['default_report']
        INFO = self._get_report_mapping_info()[default_report]
        action_xid = INFO['action_xid']
        return self._action_server_open_tl_report_wizard(action_xid)
        # default_report = self._context['default_report']
        # INFO = self._get_report_mapping_info()[default_report]
        # action = self.env.ref('addon_report.action_tl_report_wizard').sudo().read()[0]
        # action['res_id'] = self.search([('report','=', default_report),('create_uid','=', self.env.user.id)], order='id desc', limit=1).id
        # action['context'] = {'default_report': default_report, 'dc_report_wizard_id': self.id}
        # action['name'] = INFO['report_name']
        
        # return action

    def _action_server_open_tl_report_wizard(self, action_xid):
        default_report = self._context['default_report']
        INFO = self._get_report_mapping_info()[default_report]
        action = self.env.ref(action_xid).sudo().read()[0]
        action['res_id'] = self.search([('report','=', default_report),('create_uid','=', self.env.user.id)], order='id desc', limit=1).id
        action['context'] = {'default_report': default_report, 'dc_report_wizard_id': self.id}
        action['name'] = INFO['report_name']
        
        return action

    def button_open_report_list_view(self):
        INFO = self._get_report_mapping_info()[self.report]
        xmlid = INFO['report_list_view_xml_id']
        action = self.with_context(wizard_id=self.id).env.ref(xmlid).sudo().read()[0]
        action['context'] = {'wizard_id': self.id}
        # model = INFO['model']
        # self.env[model].init_data(self)
        return action

    # def download_xlsx(self):
    #     xmlid = self._get_report_mapping_info()[self.report]['aeroo_report_xml_id']
    #     action = self.env.ref(xmlid).sudo().read()[0]
    #     return action
         
    # def _get_lines(self):
    #     model = self._get_report_mapping_info()[self.report]['model']
    #     return self.env[model].with_context(wizard_id=self.id).search([])

    # def get_name_report(self):
    #     return self._get_report_mapping_info()[self.report]['report_name']

class ReportWizard(models.TransientModel):
    _name = 'tl.report.wizard'
    _inherit ='tl.report.wizard.common'
    _description = 'Report Wizard'


    def button_open_report_list_view(self):
        INFO = self._get_report_mapping_info()[self.report]
        xmlid = INFO['report_list_view_xml_id']
        action = self.with_context(wizard_id=self.id).env.ref(xmlid).sudo().read()[0]
        # action['context'] = {'dc_wizard_id': self.id}
        model = INFO['model']
        self.env[model].init_data(self)# cần phải lọc thêm create_uid
        return action

        
    def _get_report_mapping_info(self):
        rs = super()._get_report_mapping_info()
        rs.update({
            'crm_report':{
                'action_xid':'addon_report.action_tl_report_wizard',
                'model': 'crm.product.line.report',
                'report_list_view_xml_id': 'dc_crm1.action_crm_product_line_report',
                'confirm': 'init_data',
                'report_name': _('BC CRM')
            },
         
        }) 
        return rs


class CRMFilterWizard(models.TransientModel):
    _name = 'crm.filter.wizard'
    _inherit ='tl.report.wizard.common'
    _description = 'crm.filter.wizard'

    product_ids = fields.Many2many('product.product')
    categ_ids = fields.Many2many('product.category')


    def _get_report_mapping_info(self):
        rs = super()._get_report_mapping_info()
        rs.update({
            'crm_filter':{
                'action_xid':'addon_report.action_crm_filter_wizard',
                'model': 'crm.product.line.report',
                'report_list_view_xml_id': 'crm.crm_lead_opportunities_tree_view',
                # 'confirm': 'init_data',
                # 'aeroo_report_xml_id':'addon_purchase_report.action_purchase_report_report_aeroo',
                'report_name': _('Filter CRM')
            },
            # 'purchase_detail_report':{
            #     'model': 'purchase.detail.report',
            #     'report_list_view_xml_id': 'addon_purchase_report.action_purchase_detail_report_view',
            #     'aeroo_report_xml_id':'addon_purchase_report.action_purchase_detail_report_report_aeroo',
            #     'report_name': _('Purchase Detail Report')
            # }
        }) 
        return rs

    def dc_gen_domain(self):
        domain = []
        if self.product_ids:
            domain += [('order_line.product_id','in', self.product_ids.ids)]
        if self.categ_ids:
            domain += [('order_line.categ_id','in', self.categ_ids.ids)]
        return domain

    def button_open_report_list_view(self):
        INFO = self._get_report_mapping_info()[self.report]
        xmlid = INFO['report_list_view_xml_id']
        action = self.with_context(wizard_id=self.id).env.ref(xmlid).sudo().read()[0]
        action['context'] = {'dc_wizard_id': self.id}
        action['domain'] = self.dc_gen_domain()
        # model = INFO['model']
        # self.env[model].init_data(self)
        return action

        


