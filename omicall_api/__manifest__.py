# -*- coding: utf-8 -*-


{
    'name': "API",
    'summary': """Api""",
    'description': """
        Long description of module's purpose
    """,
    'author': "",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base','crm','sale','addon_report'],
    'data': [
        'security/ir.model.access.csv',
        'data/dc_selection.xml',
        'data/cronjob_api.xml',
        'views/res_company.xml',
        'views/omicall_history.xml',
        'views/res_partner.xml',
        'views/crm_lead.xml',
        'views/res_config_settings_views.xml',
        'wizards/omicall_wizard.xml',
        'wizards/create_partner_crm_wizard.xml',

        
    ],

    # 'qweb': [
    #     #'static/src/xml/*.xml',
    #     'static/src/xml/btn_tree_wine_api.xml', # <-- khai bao thua ke qweb vua hien thuc
    # ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
