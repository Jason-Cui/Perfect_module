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
import xlrd,base64
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class qdodoo_car_selecte(models.Model):
    """
        运营报表
    """
    _name = 'qdodoo.car.selecte'
    _rec_name = 'start_date'

    start_date = fields.Date(u'开始日期', required=True, default=lambda self:fields.date.today().replace(day=1))
    end_date = fields.Date(u'截止日期', required=True, default=fields.date.today())
    order_line = fields.One2many('qdodoo.car.selecte.line','order_id',u'明细')

    @api.one
    def but_search_date(self):
        # 清空原有数据
        self.search([('id','!=',self.id)]).unlink()
        self.env['qdodoo.car.selecte.line'].search([]).unlink()
        car_obj = self.env['qdodoo.car.information']
        issuing_obj = self.env['qdodoo.car.issuing.manager']
        invoice_obj = self.env['qdodoo.car.make.invoice']
        car_ids = car_obj.search([('issuing_date','>=',self.start_date),('issuing_date','<=',self.end_date)])
        over_issuing = len(issuing_obj.search([('state','!=','draft'),('issuing_date','>=',self.start_date),('issuing_date','<=',self.end_date)]).ids)
        issuing_payment_money = 0
        for line in car_obj.search([('issuing_id','!=',False),('issuing_id.state','=','doing'),('issuing_date','>=',self.start_date),('issuing_date','<=',self.end_date)]):
            issuing_payment_money += line.invoice_issuing_money
        issuing_money = 0
        for line in car_ids:
            issuing_money += line.issuing_money
        issuing_car_number = len(car_ids.ids)
        in_port_number = len(car_obj.search([('in_ship','>=',self.start_date),('in_ship','<=',self.end_date)]).ids)
        bill_car_number = len(car_obj.search([('out_stock','>=',self.start_date),('out_stock','<=',self.end_date)]).ids)
        invoice_money = 0
        for line in invoice_obj.search([('state','=','done'),('date','>=',self.start_date),('date','<=',self.end_date)]):
            invoice_money += line.all_money
        return self.write({'order_line':[(0,0,{'over_issuing':over_issuing,'issuing_money':issuing_money,'issuing_car_number':issuing_car_number,
                                        'in_port_number':in_port_number,'bill_car_number':bill_car_number,'invoice_money':invoice_money})]})

class qdodoo_car_selecte_line(models.Model):
    """
        报表明细
    """
    _name = 'qdodoo.car.selecte.line'

    order_id = fields.Many2one('qdodoo.car.selecte',u'运营报表')
    over_issuing = fields.Float(u'已开证数量')
    issuing_money = fields.Float(u'开证金额')
    issuing_payment_money = fields.Float(u'开证资金占用')
    issuing_car_number = fields.Float(u'开证车辆数')
    in_port_number = fields.Float(u'到港车辆数')
    bill_car_number = fields.Float(u'提车车辆数')
    invoice_money = fields.Float(u'已开票金额')