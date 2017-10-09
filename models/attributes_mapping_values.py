# -*- coding: utf-8 -*-

from openerp import api, exceptions, fields, models, _


class AttributesMappingValues(models.Model):
    _name = 'attributes.mapping.values'
    _description = 'Map field from sql server to field in odoo'

    name = fields.Char(string='Name', size=64, help='Field name from sql server')
    models_mapping_id = fields.Many2one(comodel_name='models.mapping.values', string='Models Mapping')
    model_id = fields.Many2one(comodel_name='ir.model', string='Models', help='Odoo Models', related='models_mapping_id.model_id')
    fields_id = fields.Many2one(comodel_name='ir.model.fields', string='Fields', domain="[('model_id', '=', model_id)]")
