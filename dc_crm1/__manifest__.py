# -*- encoding: utf-8 -*-
{
    'name': "CRM 1 DC",
    'version': '12.0.0',
    'summary': 'CRM 1 DC',
    'category': 'Other',
    'description': """CRM 1 DC""",
    'author': 'D4',
    "depends": ['base','crm','sale_crm','omicall_api','sale','addon_report'],
    'data': [
             'security/ir.model.access.csv',
            #  'demo/product_demo.xml',
            #  'demo/crm1_demo.xml',
             'data/cron_job.xml',
             'data/crm_other_data.xml',
             'data/action_server.xml',
             'data/ir_parameter_data.xml',
             'data/other.xml',
             'data/data_crm_stage.xml',
             'data/dc_selection.xml',
             'reports/crm_product_line_report_views.xml',
             
             'views/crm/search_crm_lead_views.xml',
             'views/crm/tree_crm_lead_views.xml',
             'views/crm/form_crm_lead_views.xml',
             'views/res_partner/form_res_partner.xml',
            #  'views/crm_product_line_view.xml',
            #  'views/res_config_settings_views.xml',
            #  'wizards/omicall_wizard.xml',
            #  'wizards/create_partner_crm_wizard.xml',
             'wizards/create_so_wizard_view.xml',
             ],
    "images": ["static/description/screen1.png"],
    'license': 'LGPL-3',
    'qweb': [
            ],

    'installable': True,
    'application': False,
    'auto_install': True,
}
