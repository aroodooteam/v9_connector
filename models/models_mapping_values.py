# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)
from openerp import api, exceptions, fields, models, _


el_req = {
    '0' : 'partner_title',
    '1' : 'partner_customer',
    '2' : 'partner_apporteur_a',
    '3' : 'partner_apporteur_b',
    '4' : 'product',
    '5' : 'tax_te',
    '6' : 'tax_tva',
    '7' : 'journal',
    '8' : 'account',
    '9' : 'invoice_line',
    '10' : 'invoice',
    '11' : 'partner_ag',
    '12' : 'partner_sa',
}
code_gra = ['02', '07', '19', '27', '28', '30', '74', '80', '85', '86', '93']
code_sa = [
    '01', '04', '05', '06', '09', '10', '12', '13', '15', '17', '1T', '21',
    '22', '23', '25', '26', '29', '2D', '31', '33', '34', '37', '38', '39',
    '3F', '42', '43', '44', '45', '46', '47', '48', '49', '4M', '51', '52',
    '54', '55', '56', '57', '5A', '60', '62', '63', '64', '65', '67', '68',
    '69', '6U', '71', '72', '73', '75', '76', '82', '83', '87', '88', '89',
    '98']
map_code_sa = {
    '09': '99', '1T': '11', '60': '50', '62': '61', '63': '61', '64': '61',
    '65': '18', '67': '03', '68': '18', '69': '03', '5A': '61', '25': '20',
    '26': '20', '21': '20', '22': '20', '23': '20', '29': '20', '2D': '50',
    '98': '11', '10': '99', '13': '11', '12': '99', '15': '11', '17': '11',
    '55': '53', '54': '53', '57': '50', '56': '50', '51': '50', '52': '50',
    '6U': '32', '88': '99', '89': '40', '82': '11', '83': '20', '87': '40',
    '01': '18', '06': '11', '04': '11', '49': '40', '46': '40', '47': '50',
    '44': '40', '45': '40', '42': '11', '43': '40', '3F': '20', '76': '70',
    '75': '70', '4M': '40', '73': '16', '72': '16', '71': '70', '39': '20',
    '38': '32', '48': '50', '33': '03', '31': '11', '05': '11', '37': '11',
    '34': '11'}


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
            logger.info('res1 = %s' % res)
            res = self.map_dict(res)
            logger.info('res2 = %s' % res)
            # # uniq_field = self.get_uniq_field()
            rel_field = self.get_relationnal_field()
            logger.info('res_field = %s' % rel_field)
            if rel_field[0]:
                res = self.recompute_dict_with_related_field(res, rel_field[0])
                # logger.info('=== data = %s' % res)
            # # logger.info('=== uniq_field = %s' % uniq_field)
            # # # self.insert_dict(res, uniq_field[0], rel_field[0])
            # # self.insert_dict(res, rel_field[0])
            # logger.info('=== data = %s' % res)
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
        # trying to fix m2m field
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
                if k.fields_id.ttype in ('many2many','one2many'):
                    m2m = []
                    if str(k.fields_id.name) in val:
                        # convert value to list
                        m2m.append(val.get(str(k.fields_id.name)))
                        m2m.append(arg.get(k.name, False))
                    else:
                        m2m = arg.get(k.name, False)
                    val.update({
                        str(k.fields_id.name): m2m,
                    })
                else:
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
                            'model': k.rel_model_id.model,
                            'type': k.fields_id.ttype
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
                    # manage m2m and o2m value
                    # if v.get('type', False) in ('many2many', 'one2many'):
                    #     domain = v.get('domain') % val.get(k)
                    #     domain = eval(domain)
                    #     for elt in val.get(k, False):
                    #         domain = v.get('domain') % elt
                    #         domain = eval(domain)
                    #         dyn_ids = dyn_obj.search(domain)
                    #         logger.info('=== dyn_ids_m2m = %s' % dyn_ids)

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
                    # if v.get('type', False) in ('many2many', 'one2many'):
                    elif dyn_ids and len(dyn_ids) > 1:
                        if v.get('type', False) in ('many2many', 'one2many'):
                            # convert value
                            val[k] = [(6, 0, tuple(dyn_ids.ids))]
                        else:
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
        inv_model = self.env.ref('account.model_account_invoice')
        for val in vals:
            domain = val.pop('domain')
            logger.info('== %s val = %s' % (tt, val))
            model_obj = self.env[self.model_id.model]
            if domain:
                src_ids = model_obj.search(domain)
                logger.info('src_ids = %s' % src_ids)
                if self.model_id == inv_model:
                    if self._context.get('reset_taxes', False):
                        # create nothing just update tax
                        if not src_ids:
                            logger.info('src_ids inexistant')
                        else:
                            src_ids.button_reset_taxes()
                    # open invoice
                    elif self._context.get('invoice_open', False):
                        # create nothing just open invoice
                        if not src_ids:
                            logger.info('src_ids inexistant')
                        else:
                            src_ids.signal_workflow('invoice_open')
                    else:
                        # control invoice account and data
                        # logger.info('=== 0 - val = %s===' % val)
                        # update account_id in val
                        self.check_account(val)
                        # logger.info('=== 1 - val = %s===' % val)
                        if not src_ids:
                            model_obj.create(val)
                        elif src_ids and len(src_ids) == 1:
                            src_ids.write(val)
                else:
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

    @api.multi
    def button_reset_taxes(self):
        ctx = self._context.copy()
        ctx.update({'reset_taxes': True})
        self.with_context(ctx).import_data()

    @api.multi
    def invoice_open(self):
        ctx = self._context.copy()
        ctx.update({'invoice_open': True})
        self.with_context(ctx).import_data()

    # TODO
    @api.multi
    def check_account(self, vals):
        acc_obj = self.env['account.account']
        if vals.get('account_id', False) in code_gra:
            vals['account_id'] = acc_obj.search([('code','=','411100')]).id
        else:
            vals['account_id'] = acc_obj.search([('code','=','410000')]).id
        # return False

    @api.multi
    def insert_with_internal_control(self):
        return False
