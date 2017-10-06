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
    driver = fields.Char(string='Driver', help='Help note')
    driver = fields.Selection(selection=[('FreeTDS', 'FreeTDS'),('other', 'Other')], string='Driver', help='Choose Driver')
    version = fields.Char(string='Driver Version', size=64, help='TDS_Version')
    active = fields.Boolean(string='Active', help='Active', default=True)
