# -*- coding: utf-8 -*-
{
    'name': 'Mailcow Integration',
    'version': '1.0.0',
    'category': 'Extra Tools',
    'summary': 'Module for integrating Mailcow email server with Odoo.',
    'description': """
Mailcow Integration
===================

This module integrates the Mailcow email server with Odoo, providing a seamless email communication solution for your Odoo instance. It allows for syncing of mailboxes and email aliases from Mailcow to Odoo and vice versa.

Main Features:
--------------
* Synchronize Mailcow mailboxes with Odoo users.
* Synchronize Mailcow email aliases with Odoo.
* Configuration of Mailcow API credentials in Odoo settings.
* Automatically create and manage mailboxes and aliases in Mailcow when they are created in Odoo.
""",
    'sequence': 10,
    'license': 'OPL-1',
    'author': 'BeMade',
    'website': 'https://www.bemade.org',
    'depends': ['hr', 'mail', 'bemade_user_password_bundle'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/mailcow_mailbox_views.xml',
        'views/mailcow_alias_views.xml',
        'views/mailcow_blacklist_views.xml',
        'views/res_users_views.xml',

    ],
    "assets": {
        "web.assets_backend": [
            "bemade_mailcow_blacklist/static/src/js/mailcow_mailbox.js",
            "bemade_mailcow_blacklist/static/src/js/mailcow_alias.js",
            "bemade_mailcow_blacklist/static/src/js/mailcow_blacklist.js",
        ],
        "web.assets_qweb": [
            "bemade_mailcow_blacklist/static/src/xml/mailcow_mailbox.xml",
            "bemade_mailcow_blacklist/static/src/xml/mailcow_alias.xml",
            "bemade_mailcow_blacklist/static/src/xml/mailcow_blacklist.xml",
        ],
    },
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
