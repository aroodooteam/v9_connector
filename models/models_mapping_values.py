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
            logger.info('res = %s' % res)
            # # uniq_field = self.get_uniq_field()
            rel_field = self.get_relationnal_field()
            logger.info('res_field = %s' % rel_field)
            if rel_field[0]:
                res = self.recompute_dict_with_related_field(res, rel_field[0])
                logger.info('=== data = %s' % res)
            # logger.info('=== uniq_field = %s' % uniq_field)
            # # self.insert_dict(res, uniq_field[0], rel_field[0])
            # self.insert_dict(res, rel_field[0])
            self.insert_dict(res)
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
        domain = False
        final_dom = []
        for arg in args:
            final_dom = []
            for k in self.attributes_ids:
                # logger.info('=== %s, %s => %s' % (k.name, k.fields_id.name, arg.get(k.name)))
                if k.check_unicity and k.current_criteria:
                    if arg.get(k.name,False) not in (None, False):
                        domain = k.current_criteria % arg.get(k.name,False)
                    else:
                        domain = '[]'
                    final_dom += eval(domain)
                val.update({
                    str(k.fields_id.name): arg.get(k.name, False),
                })
            val.update({'domain': final_dom})
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
            if not k.check_unicity and k.check_rel_field:
                val.update(
                    {
                        k.fields_id.name: {
                            'domain': k.related_criteria,
                            'model': k.rel_model_id.model
                        }
                    }
                )
        res.append(val)
        return res

    @api.multi
    def recompute_dict_with_related_field(self, vals, rel_dict={}):
        res = []
        if not rel_dict:
            return res
        for val in vals:
            # buf_val = {}
            for k,v in rel_dict.iteritems():
                if k in val and val.get(k, False):
                    dyn_obj = self.env[v.get('model')]
                    domain = v.get('domain') % val.get(k)
                    domain = eval(domain)
                    # logger.info('computed_loop_domain = %s' % domain)
                    dyn_ids = dyn_obj.search(domain)
                    logger.info('=== dyn_ids = %s' % dyn_ids)
                    if not dyn_ids:
                        "Create new record to fix it"
                        logger.info('=== Error: no data found for %s with domain = %s' % (v.get('model'), domain))
                        raise exceptions.Warning(
                            _('Error'),
                            _("No data found for %s with domain = %s" % (v.get('model'), domain))
                        )
                    elif dyn_ids and len(dyn_ids) > 1:
                        "Verify the correct record to fix it"
                        logger.info('=== Error: to much data found for %s with domain = %s' % (v.get('model'), domain))
                        raise exceptions.Warning(
                            _('Error'),
                            _("To much data found for %s with domain = %s" % (v.get('model'), domain))
                        )
                    else:
                        val[k] = dyn_ids.id
            res.append(val)
        return res

    @api.multi
    def insert_dict(self, vals, rel_crit={}):
        if not vals:
            logger.info('=== nothing to insert')
            return False
        if not rel_crit:
            logger.info('=== no criteria')
        logger.info('=== vals = %s' % len(vals))
        tt = len(vals)
        # logger.info('=== rel_crit = %s' % rel_crit)
        for val in vals:
            domain = val.pop('domain')
            logger.info('== %s val = %s' % (tt, val))
            model_obj = self.env[self.model_id.model]
            if domain:
                src_ids = model_obj.search(domain)
                logger.info('src_ids = %s' % src_ids)
                if not src_ids:
                    model_obj.create(val)
                elif src_ids and len(src_ids) == 1:
                    src_ids.write(val)
            tt -= 1

        # domain = False
        # for k,v in uniq_crit.iteritems():
        #     domain = v
        #     logger.info('%s, %s' %(k,v))
        # for val in vals:
        #     logger.info('=== domain = %s' % domain)
        #     src_ids = self.model_id.search(domain)
        #     logger.info('src_ids = %s' % src_ids)
        #     # if not src_ids:
        #         # self.model_id.create(val)

    # @api.multi
    # def compute_domain(self, vals,)
