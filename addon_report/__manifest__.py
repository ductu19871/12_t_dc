# -*- coding: utf-8 -*-
{
    'name': 'Addon Report',
    'category': '',
    'author': 'TLTEK',
    'author_email': 'Ductu',    
    'depends': ['base','product','crm'],
    'data': [
        'security/ir.model.access.csv',
        # 'data/dc_selection.xml',
        'wizard/tl_report_wizard_view.xml',
        'wizard/crm_filter_wizard.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
