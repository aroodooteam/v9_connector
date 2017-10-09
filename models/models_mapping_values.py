# -*- coding: utf-8 -*-

from openerp import api, exceptions, fields, models, _


class ModelsMappingValues(models.Model):
    _name = 'models.mapping.values'
    _description = 'The Models and list of fields to import into Odoo'

    name = fields.Char(string='Name')
    sql_model = fields.Char(string='Object to map', help='Name of the model to import from SQL Server')
    model_id = fields.Many2one(comodel_name='ir.model', string='Model', help='Destination model')
    attributes_ids = fields.One2many(comodel_name='attributes.mapping.values', inverse_name='models_mapping_id', string='Attributes', help='Set Mappings')
    comments = fields.Text(string='Comments')
    server_id = fields.Many2one(comodel_name='parameter.setting', string='Server')

    @api.multi
    def import_data(self):
        """Import Data corresponding to the current model"""
        return True
