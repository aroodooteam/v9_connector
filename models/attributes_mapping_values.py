# -*- coding: utf-8 -*-

from openerp import api, exceptions, fields, models, _


class AttributesMappingValues(models.Model):
    _name = 'attributes.mapping.values'
    _description = 'Map field from sql server to field in odoo'

    name = fields.Char(string='Name', size=64, help='Field name from sql server')
    models_mapping_id = fields.Many2one(comodel_name='models.mapping.values', string='Models Mapping')
    model_id = fields.Many2one(comodel_name='ir.model', string='Models', help='Odoo Models', related='models_mapping_id.model_id')
    check_rel_field = fields.Boolean(string='Check Related field', help=u'Don\'t insert data if allready exist')
    rel_model_id = fields.Many2one(comodel_name='ir.model', string='Related Model')
    fields_id = fields.Many2one(comodel_name='ir.model.fields', string='Fields', domain="[('model_id', '=', model_id)]")
    check_unicity = fields.Boolean(string='Check unicity', help=u'Don\'t insert data in allready exist')
    operator = fields.Selection(selection=[('&', 'And'),('|', 'Or')], string='operator')
    related_criteria = fields.Char(string='Relationnal field Domain', help=u'Domain to use in case of relationnal field need to be converted in DB id')
    current_criteria = fields.Char(string='Current Model Domain', help=u'Domain to use in current target model to search if data allready exist in case of <Check unicity> is checked')
