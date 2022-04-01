# -*- coding: utf-8 -*-
{
    'name': 'Send Whatsapp Message',
    'version': '14.0.1.0.1',
    'summary': 'Send Message to partner via Whatsapp web',
    'description': 'Send Message to partner via Whatsapp web',
    'category': 'Extra Tools',
    'author': 'Vira Web 123',
    'maintainer': 'Vira Web 123',
    'company': 'Vira Web 123',
    'website': 'https://viraweb123.ir',
    'depends': [
        'base',
        'contacts'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/view.xml',
        'wizard/wizard.xml',
    ],
    'images': [
        'static/description/banner.png'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
