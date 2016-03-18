# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for Qdodoo suifeng
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models, api
from openerp.osv import osv
from openerp.tools.translate import _
from datetime import timedelta, datetime
import logging
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class qdodoo_car_port_manager(models.Model):
    """
        港口管理
    """
    _name = 'qdodoo.car.port.manager'
    _order = 'id desc'

    name = fields.Char(u'港口')
    type = fields.Selection([('out',u'发货港'),('in',u'目的港')],u'类型')
    country_id = fields.Many2one('res.country',u'国家')

class qdodoo_car_expense(models.Model):
    """
        费用项目
    """
    _name = 'qdodoo.car.expense'
    _order = 'id desc'

    name = fields.Char(u'费用名称', required=True)
    car_name = fields.Char(u'车辆档案条目', required=True)
    bill_name = fields.Char(u'提车款条目', required=True)
    expense_type = fields.Selection([('translation',u'运输费'),('receivable',u'应收款'),('old_receivable',u'预收款'),('payable',u'应付款')],u'费用类型', required=True)


