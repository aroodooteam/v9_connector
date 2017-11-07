# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)
from openerp import api, exceptions, fields, models, _


class ModelsMappingValues(models.Model):
    _name = 'models.mapping.values'
    _description = 'The Models and list of fields to import into Odoo'

    name = fields.Char(string='Name')
    sql_model = fields.Char(string='Object to map', help='Name of the model to import from SQL Server')
    model_id = fields.Many2one(comodel_name='ir.model', string='Model', help='Destination model in Odoo')
    attributes_ids = fields.One2many(comodel_name='attributes.mapping.values', inverse_name='models_mapping_id', string='Attributes', help='Set Mappings')
    comments = fields.Text(string='Comments')
    sql_request = fields.Text(string='SQL Request')
    server_id = fields.Many2one(comodel_name='parameter.setting', string='Server')

    @api.multi
    def import_data(self):
        """Import Data corresponding to the current model"""
        logger.info('=== import data => sql = %s' % self.sql_request)
        con = self.server_id.connect()
        logger.info('=== con = %s' % con)
        cr_sql = False
        if con:
            try:
                cr_sql = con.cursor()
                cr_sql.execute(self.sql_request)
                logger.info('=== Everything is Ok')
            except Exception, e:
                raise exceptions.Warning(
                    _('Error'),
                    _('Can\'t execute SQL request %s' % e))
        if cr_sql:
            res = self.map_sql_todict(cr_sql)
            res = self.map_dict(res)
            uniq_field = self.get_uniq_field()
            rel_field = self.get_relationnal_field()
            logger.info('=== uniq_field = %s' % uniq_field)
            self.insert_dict(res, uniq_field[0], rel_field[0])
        return True

    @api.multi
    def map_sql_todict(self, cr_sql=None):
        if not cr_sql:
            return False
        res = []
        columns = [column[0] for column in cr_sql.description]
        for row in cr_sql.fetchall():
            res.append(dict(zip(columns,row)))
        return res

    @api.multi
    def map_dict(self, args=[]):
        if not args:
            return []
        res = []
        val = {}
        for arg in args:
            for k in self.attributes_ids:
                # logger.info('=== %s, %s => %s' % (k.name, k.fields_id.name, arg.get(k.name)))
                val.update({
                    str(k.fields_id.name): arg.get(k.name, False)
                })
            res.append(val)
            val = {}
        return res

    @api.multi
    def get_uniq_field(self):
        """ Only for current model """
        res = []
        val = {}
        for k in self.attributes_ids:
            if k.check_unicity:
                val.update({k.fields_id.name: k.current_criteria})
        res.append(val)
        return res

    @api.multi
    def get_relationnal_field(self):
        res = []
        val = {}
        for k in self.attributes_ids:
            if not k.check_unicity and k.related_criteria:
                val.update({k.fields_id.name: k.related_criteria})
        res.append(val)
        return res

    @api.multi
    def insert_dict(self, vals, uniq_crit={}, rel_crit={}):
        if not vals:
            logger.info('=== nothing to insert')
            return False
        if not uniq_crit and not rel_crit:
            logger.info('=== no criteria')
        logger.info('=== vals = %s' % vals)
        domain = False
        for k,v in uniq_crit.iteritems():
            domain = v
            logger.info('%s, %s' %(k,v))
        for val in vals:

            src_ids = self.model_id.search(domain)
            logger.info('src_ids = %s' % src_ids)
            if not src_ids:
                self.model_id.create(val)
