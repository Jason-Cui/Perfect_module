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
class qdodoo_car_pad_tax(models.Model):
    """
        垫税
    """
    _name = 'qdodoo.car.pad.tax'    # 模型名称
    _order = 'id desc'

    name = fields.Char(u'申请单号')
    purchase_id = fields.Many2one('qdodoo.car.purchase.contract',u'外贸合同号')
    # bill_id = fields.Many2one('qdodoo.car.bill.lading',u'提单号')
    date = fields.Date(u'日期',default=lambda self:datetime.now().date())
    order_line = fields.One2many('qdodoo.car.pad.tax.line','pad_id',u'货物明细')
    state = fields.Selection([('draft', u'草稿'),('doing',u'登账'),('done', u'完成'),('cancel', u'取消')], u'状态',default='draft')
    car_number = fields.Float(u'数量',compute='_get_car_number')

    def _get_car_number(self):
        for ids in self:
            ids.car_number = 0
            for line in ids.order_line:
                ids.car_number += 1

    # 根据外贸合同获取车辆明细
    @api.onchange('purchase_id')
    def _get_order_lie(self):
        self.order_line = ''
        lst = []
        for line in self.env['qdodoo.car.information'].search([('purchase_id','=',self.purchase_id.id)]):
            if not line.pad_id:
                lst.append((0,0,{'in_issuing_money':line.in_issuing_money,'delayed_moeny':line.delayed_moeny,'product_id':line.product_id.id,'product_num':line.id,'pad_agent':line.pad_agent,
                                'tax_id':line.tax_id,'in_tax':line.in_tax,'in_sale_tax':line.in_sale_tax,'add_tax':line.add_tax,
                                'pad_money':line.pad_money,'pad_tax_date':line.pad_tax_date,'pad_tax_end_date':line.pad_tax_end_date}))
        self.order_line = lst

    # 获取唯一的编号
    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].get('qdodoo.car.pad.tax')
        return super(qdodoo_car_pad_tax, self).create(vals)

    # 确认
    @api.one
    def btn_doing(self):
        return self.write({'state':'doing'})

    # 取消
    @api.one
    def btn_cancel(self):
        return self.write({'state':'cancel'})

    # 登账
    @api.one
    def btn_done(self):
        return self.write({'state':'done'})

class qdodoo_car_pad_tax_line(models.Model):
    _name = 'qdodoo.car.pad.tax.line'

    pad_id = fields.Many2one('qdodoo.car.pad.tax',u'垫税单')
    product_id = fields.Many2one('product.product',u'车辆型号')
    product_num = fields.Many2one('qdodoo.car.information',u'车架号')
    pad_agent = fields.Float(u'垫税代理费')
    tax_id = fields.Char(u'税单号')
    in_tax = fields.Float(u'进口关税')
    in_sale_tax = fields.Float(u'进口消费税')
    add_tax = fields.Float(u'进口增值税')
    delayed_moeny = fields.Float(u'滞报金')
    in_issuing_money = fields.Float(u'海关保证金')
    note = fields.Text(u'备注')
    pad_money = fields.Float(u'垫税金额',compute="_get_pad_money")
    pad_tax_date = fields.Date(u'垫税日期')
    pad_tax_end_date = fields.Date(u'垫税截止日期')

    # 获取垫税金额
    def _get_pad_money(self):
        for ids in self:
            ids.pad_money = ids.in_tax + ids.in_sale_tax + ids.add_tax + ids.delayed_moeny + ids.in_issuing_money

