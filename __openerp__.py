# -*- coding: utf-8 -*-

{
    "name": 'V9 connector',
    "version": "0.1",
    "depends": [
        'account',
        'account_invoice_inherit',
        'analytic',
        'base',
        'commission',
        'insurance_management',
        'product',
    ],
    "author": "Rakotomalala Haritiana <haryoran04@gmail.com>",
    "category": "Tools",
    "installable": True,
    "data": [
        'views/parameter_setting_view.xml',
        'views/models_mapping_values_view.xml',
        'data/setting_data.xml',
        'data/model_mapping_values_data.xml',
        'data/model_mapping_values_data_new.xml',
        'wizard/policy_generator_view.xml',
    ],
}
