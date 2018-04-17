# -*- coding: utf-8 -*-


from openerp import api, exceptions, fields, models, _
import logging
logger = logging.getLogger(__name__)


class PolicyGenerator(models.TransientModel):
    _name = 'policy.generator'
    _description = 'Generate contract from invoice'

    max_number = fields.Integer(string='Maximum', default='1')
    period_id = fields.Many2one(comodel_name='account.period', string='Period', domain="[('special','=', False)]")
    period_ids = fields.Many2many(comodel_name='account.period', string='Periods',  domain="[('special','=', False)]")
    run_multiperiod = fields.Boolean(string='Run multi periods')

    @api.onchange('period_id')
    def GetMaxNumber(self):
        inv_obj = self.env['account.invoice']
        inv_ids = inv_obj.search([('period_id', '=', self.period_id.id)])
        self.max_number = len(inv_ids)

    @api.multi
    def GeneratePolicy(self):
        if not self.run_multiperiod and not self.period_id:
            # if not self.period_id:
            return False
        if self.run_multiperiod and not self.period_ids:
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
        if not self.run_multiperiod:
            if self.max_number:
                inv_src = inv_obj.search([('period_id', '=', self.period_id.id)], limit=self.max_number)
            else:
                inv_src = inv_obj.search([('period_id', '=', self.period_id.id)])
        else:
            inv_src = inv_obj.search([('period_id', 'in', self.period_ids.ids)])
        # map policy from invoice
        pol_val = []
        if inv_src:
            inv_rds = inv_src.read(inv_field)
            for inv_rd in inv_rds:
                buf_val = {'is_insurance': True, 'type': 'view'}
                # search branch and product from inv_line
                complement_analytic = self.GetBranch(inv_rd.get('id', False))
                buf_val.update(complement_analytic)
                logger.info('buf_val = %s' % buf_val)
                for k,v in inv_rd.iteritems():
                    if k not in ('final_customer_id', 'id'):
                        buf_val[map_polinv.get(k)] = v
                    elif k == 'final_customer_id':
                        buf_val[map_polinv.get(k)] = v[0]
                        buf_val['insured_id'] = v[0]
                logger.info('buf_val2 = %s' % buf_val)
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
        i = 0
        for vals in vals_list:
            i += 1
            logger.info('=== loops search policy %s / %s' % (i, len(vals_list)))
            pol_ids = pol_obj.search([('name', '=', vals.get('name'))])
            if not pol_ids:
                res.append(pol_ids.create(vals).ids[0])
            else:
                res += pol_ids.ids
                # pol_ids.update(vals)
        res = list(set(res))
        return res

    @api.multi
    def GetBranch(self, inv_id):
        if not inv_id:
            return False
        # logger.info('inv = %s' % inv_id)
        res = {}
        inv_line_obj = self.env['account.invoice.line']
        inv_line_ids = inv_line_obj.search([('invoice_id', '=', inv_id)])
        for inv_line_id in inv_line_ids:
            if inv_line_id.product_id.branch_id and inv_line_id.product_id.ins_product_id:
                res['branch_id'] = inv_line_id.product_id.branch_id.id
                res['ins_product_id'] = inv_line_id.product_id.ins_product_id.id
                break
        if res:
            return res
        return False

    @api.multi
    def GenerateVersion(self):
        """Run only after GeneratePolicy"""
        pol_obj = self.env['account.analytic.account']
        hist_obj = self.env['account.analytic.account']
        inv_obj = self.env['account.invoice']
        values = self.GeneratePolicy()
        # logger.info('\n === values = %s' % values)
        policies = values.get('policy', [])
        res = []
        i = 0
        for policy in pol_obj.browse(policies):
            i += 1
            logger.info('%s -> %s (%s / %s)' % (policy.name, policy.id, i, len(policies)))
            # search invoice
            inv_ids = inv_obj.search([('pol_numpol', '=', policy.name), ('id','in', values.get('invoice'))], order='prm_datedeb')
            # logger.info('=== inv_ids = %s' % inv_ids.mapped('prm_datedeb'))
            inv_len = len(inv_ids)
            c = 0
            for inv_id in inv_ids:
                c += 1
                # logger.info('inv_len = %s ?= %s c' % (inv_len,c))
                hist_buf = {
                    'type': 'contract',
                    'is_insurance': True,
                    'partner_id': policy.partner_id.id,
                    'property_account_position': policy.property_account_position.id,
                    'insured_id': policy.insured_id.id,
                    'manager_id': policy.manager_id.id,
                    'branch_id': policy.branch_id.id,
                    'ins_product_id': policy.ins_product_id.id,
                    'fraction_id': policy.fraction_id.id or False,
                    'name': policy.name + '_' + str(c).zfill(4),
                    'parent_id': policy.id,
                    'date_start': inv_id.prm_datedeb,
                    'date': inv_id.prm_datefin,
                    'agency_id': inv_id.journal_id.agency_id.id or False,
                    'invoice_id': inv_id.id,
                    'stage_id': self.env.ref('insurance_management.avenant').id
                }
                if c == inv_len:
                    hist_buf['is_last_situation'] = True
                hist_ids = hist_obj.search([('name','=', hist_buf.get('name'))])
                if not hist_ids:
                    # logger.info('===> create history')
                    res.append(hist_obj.create(hist_buf).id)
                else:
                    hist_ids.update(hist_buf)
                    res += hist_ids.ids
        return res

    @api.multi
    def GenerateRiskLine(self):
        ver_ids = self.GenerateVersion()
        # logger.info('\n === ver_ids = %s' % ver_ids)
        ver_obj = self.env['account.analytic.account']
        risk_obj = self.env['analytic_history.risk.line']
        ver_ids = ver_obj.browse(ver_ids)
        res = []
        for ver_id in ver_ids:
            risk_data = self.GetTypeRiskFromInvoice(ver_id, ver_id.invoice_id)
            logger.info('risk_data = %s' % risk_data)
            for k,v in risk_data.iteritems():
                risk_ids = risk_obj.search([('analytic_id', '=', v.get('analytic_id')),('type_risk_id', '=', v.get('type_risk_id'))])
                if not risk_ids:
                    res.append(risk_obj.create(v).id)
                else:
                    # risk_ids.update(v)
                    res += risk_ids.ids
        return res

    @api.multi
    def GetTypeRiskFromInvoice(self, ver, inv):
        if not inv:
            return False
        risk_buf = {}
        for inv_line in inv.invoice_line:
            vals_buf = {
                'analytic_id': ver.id,
                'partner_id': ver.parent_id.partner_id.id,
                'type_risk_id': inv_line.product_id.type_risk_id.id,
                'name': inv_line.name
            }
            if inv_line.product_id.type_risk_id.id not in risk_buf.keys() and inv_line.product_id.default_code not in ('ACCM','ACCT','ACCV'):
                risk_buf[inv_line.product_id.type_risk_id.id] = vals_buf
        return risk_buf

    @api.multi
    def GenerateWarrantyLine(self):
        risk_data = self.GenerateRiskLine()
        # logger.info('risk_data_wrt = %s' % risk_data)
        risk_obj = self.env['analytic_history.risk.line']
        warranty_obj = self.env['risk.warranty.line']
        risk_ids = risk_obj.browse(risk_data)
        res = []
        len_risk = len(risk_ids)
        i = 0
        for risk_id in risk_ids:
            i += 1
            logger.info('=== loop for warranty %s / %s' % (i,len_risk))
            for inv_line in risk_id.analytic_id.invoice_id.invoice_line:
                vals = {}
                if risk_id.type_risk_id == inv_line.product_id.type_risk_id:
                    vals['warranty_id'] = inv_line.product_id.id
                    vals['name'] = inv_line.product_id.name
                    vals['proratee_net_amount'] = inv_line.price_unit
                    vals['history_risk_line_id'] = risk_id.id
                    warranty_ids = warranty_obj.search([('warranty_id','=',inv_line.product_id.id),('history_risk_line_id','=',risk_id.id)])
                    if not warranty_ids:
                        res.append(warranty_obj.create(vals).id)
                    else:
                        # warranty_ids.update(vals)
                        res += warranty_ids.ids
        return res
