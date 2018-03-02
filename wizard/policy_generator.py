# -*- coding: utf-8 -*-


from openerp import api, exceptions, fields, models, _
import logging
logger = logging.getLogger(__name__)


class PolicyGenerator(models.TransientModel):
    _name = 'policy.generator'
    _description = 'Generate contract from invoice'

    max_number = fields.Integer(string='Maximum', default='1')
    period_id = fields.Many2one(comodel_name='account.period', string='Period', domain="[('special','=', False)]")

    @api.onchange('period_id')
    def GetMaxNumber(self):
        inv_obj = self.env['account.invoice']
        inv_ids = inv_obj.search([('period_id', '=', self.period_id.id)])
        self.max_number = len(inv_ids)

    @api.multi
    def GeneratePolicy(self):
        if not self.period_id:
            return False
        inv_field = ['pol_numpol', 'prm_datedeb', 'prm_datefin', 'final_customer_id']
        map_polinv = {
            'pol_numpol': 'name',
            'prm_datedeb': 'date_start',
            'prm_datefin': 'date',
            'final_customer_id': 'partner_id',
        }
        analytic_obj = self.env['account.analytic.account']
        inv_obj = self.env['account.invoice']
        # search invoice in selected period
        inv_src = False
        if self.max_number:
            inv_src = inv_obj.search([('period_id', '=', self.period_id.id)], limit=self.max_number)
        else:
            inv_src = inv_obj.search([('period_id', '=', self.period_id.id)])
        # map policy from invoice
        pol_val = []
        if inv_src:
            inv_rds = inv_src.read(inv_field)
            for inv_rd in inv_rds:
                buf_val = {'is_insurance': True}
                for k,v in inv_rd.iteritems():
                    if k not in ('final_customer_id', 'id'):
                        buf_val[map_polinv.get(k)] = v
                    elif k == 'final_customer_id':
                        buf_val[map_polinv.get(k)] = v[0]
                        buf_val['insured_id'] = v[0]
                pol_val.append(buf_val)
        res = {
            'policy': self.create_policy(pol_val),
            'invoice': inv_src.ids,
        }
        return res
        # logger.info('\n pol_val = %s' % pol_val)


    @api.multi
    def create_policy(self, vals_list):
        # check if policy allready exist
        pol_obj = self.env['account.analytic.account']
        res = []
        for vals in vals_list:
            pol_ids = pol_obj.search([('name', '=', vals.get('name'))])
            logger.info('pol_ids = %s' % pol_ids)
            if not pol_ids:
                res.append(pol_ids.create(vals))
            else:
                res += pol_ids.ids
                pol_ids.update(vals)
        res = list(set(res))
        return res

    @api.multi
    def GenerateVersion(self):
        """Run only after GeneratePolicy"""
        pol_obj = self.env['account.analytic.account']
        hist_obj = self.env['analytic.history']
        inv_obj = self.env['account.invoice']
        values = self.GeneratePolicy()
        logger.info('\n === values = %s' % values)
        policies = values.get('policy', [])
        hist_vals = []
        for policy in pol_obj.browse(policies):
            logger.info('%s -> %s' % (policy.name, policy.id))
            # search invoice
            inv_ids = inv_obj.search([('pol_numpol', '=', policy.name), ('id','in', values.get('invoice'))], order='prm_datedeb')
            logger.info('=== inv_ids = %s' % inv_ids.mapped('prm_datedeb'))
            inv_len = len(inv_ids)
            c = 0
            hist_pol = []
            for inv_id in inv_ids:
                c += 1
                logger.info('inv_len = %s ?= %s c' % (inv_len,c))
                hist_buf = {
                    'name': policy.name + '_' + str(c).zfill(4),
                    'analytic_id': policy.id,
                    'starting_date': inv_id.prm_datedeb,
                    'ending_date': inv_id.prm_datefin,
                    'agency_id': inv_id.journal_id.agency_id.id or False,
                    'invoice_id': inv_id.id,
                }
                if c == inv_len:
                    hist_buf['is_last_situation'] = True
                if not hist_obj.search([('name','=', hist_buf.get('name'))]):
                    logger.info('===> create history')
                    hist_obj.create(hist_buf)
        return True
