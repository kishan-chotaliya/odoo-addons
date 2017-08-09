# -*- coding: utf-8 -*-
{
    'name': 'Sale Order Customize',
    'author': 'Wiz@rd Technolabs',
    'category': 'Sale',
    'summary': 'Sale Orer Customization',
    'description': 'Sale order line customization.',
    'version': '1.0',
    'depends': ['sale', 'product', 'report', 'stock'],
    'data': [
            'security/ir.model.access.csv',
            'views/partner_view.xml',
            'views/product_view.xml',
            'views/company_view.xml',
            'views/sale_view.xml',
            'report/report_saleorder.xml',
            ],
    'installable': True,
    'application': True,
}
