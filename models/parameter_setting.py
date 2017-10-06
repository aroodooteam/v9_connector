# -*- coding: utf-8 -*-

import logging
import pyodbc

from openerp import models, fields, api, _
from openerp.exceptions import Warning
logger = logging.getLogger(__name__)


class ParameterSetting(models.Model):
    """Parameter for the connector"""
    _name = "parameter.setting"

    name = fields.Char(string='Name')
    host = fields.Char(string='Server', help='Put Your server adress here')
    port = fields.Char(string='Port', help='Port of database V9 to connect')
    database = fields.Char(string='Database', help='Name of the database')
    dbuser = fields.Char(string='DB User', help='User of v9 database')
    db_pass = fields.Char(string='Password', help='Put the password here')
    driver = fields.Selection(selection=[('FreeTDS', 'FreeTDS'),('other', 'Other')], string='Driver', help='Choose Driver')
    version = fields.Char(string='Driver Version', size=64, help='TDS_Version')
    active = fields.Boolean(string='Active', help='Active', default=True)
    sequence = fields.Integer(string='Priority')

    @api.multi
    def test_sqlserver_connection(self):
        logger.info('\n=== Try Connect on SQL Server ===\n')
        connection = False
        # TODO
        # Make prm driver dynamic
        prm = "DRIVER=%s;SERVER=%s;PORT=%s;DATABASE=%s;UID=%s;PWD=%s;TDS_Version=%s" % (self.driver, self.host, self.port, self.database, self.dbuser, self.db_pass, self.version)
        try:
            connection = pyodbc.connect(prm)
        except Exception, e:
            logger.info('=== %s ===' % e)
            raise Warning(_('Error'), _(u'Can\'t connect to SQL Server %s' % str(e)))
        finally:
            try:
                if connection:
                    connection.close()
            except Exception:
                pass
        raise Warning(_('Succes'), _(u'Everything seems to be correct'))

    @api.multi
    def connect(self):
        logger.info('\n=== Try Connect on SQL Server ===\n')
        connection = False
        prm = "DRIVER=%s;SERVER=%s;PORT=%s;DATABASE=%s;UID=%s;PWD=%s;TDS_Version=%s" % (self.driver, self.host, self.port, self.database, self.dbuser, self.db_pass, self.version)
        try:
            connection = pyodbc.connect(prm)
        except Exception, e:
            raise Warning(_('Error'), _(u'Can\'t connect to SQL Server %s' % str(e)))
        return connection
