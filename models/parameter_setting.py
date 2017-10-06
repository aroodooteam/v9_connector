# -*- coding: utf-8 -*-

# 1 : imports from python lib
import logging
import pyodbc

# 2 : imports from openerp
from openerp import models, fields, api, _
from openerp.exceptions import Warning
# 3 : imports from odoo modules
logger = logging.getLogger(__name__)


class ParameterSetting(models.Model):
    """Parameter for the connector"""
    _name = "parameter.setting"

    name = fields.Char(string='Server', help='Put Your server adress here')
    port = fields.Char(string='Port', help='Port of database V9 to connect')
    database = fields.Char(string='Database', help='Name of the database')
    dbuser = fields.Char(string='DB User', help='User of v9 database')
    db_pass = fields.Char(string='Password', help='Put the password here')
    driver = fields.Selection(selection=[('FreeTDS', 'FreeTDS'),('other', 'Other')], string='Driver', help='Choose Driver')
    version = fields.Char(string='Driver Version', size=64, help='TDS_Version')
    active = fields.Boolean(string='Active', help='Active', default=True)

    @api.multi
    def _get_connection(self):
        logger.info('\n=== Try Connect on SQL Server ===\n')
        connection = False
        crSQLServer = False
        # TODO
        # Make prm driver dynamic
        prm = "DRIVER=%s;SERVER=%s;PORT=%s;DATABASE=%s;UID=%s;PWD=%s;TDS_Version=%s" % (self.driver, self.name, self.port, self.database, self.dbuser, self.db_pass, self.version)
        try:
            # connection = pypyodbc.connect("DRIVER=FreeTDS;SERVER=10.0.0.92;
            # PORT=1433;DATABASE=dwh_stat;UID=sa;PWD=Aro1;TDS_Version=7.0")
            connection = pyodbc.connect(prm)
            crSQLServer = connection.cursor()
            # crSQLServer.execute(request_sql2)
        except Exception, e:
            raise Warning(_('Error'),
                                     _('Can\'t connect to SQL Server %s' % e))
        logger.info('\n=== Connected  ===\n')

        return {
            'con': connection,
            'crSQLServer': crSQLServer,
        }
