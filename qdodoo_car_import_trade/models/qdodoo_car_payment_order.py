# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for Qdodoo suifeng
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

from openerp import fields, models, api
from openerp.osv import osv
import xlrd,base64
from openerp.tools.translate import _
from datetime import timedelta, datetime
import logging
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp import SUPERUSER_ID

_logger = logging.getLogger(__name__)

class qdodoo_car_payment_order(models.Model):
    """
        收款通知
    """
    _name = 'qdodoo.car.payment.order'
    _order = 'id desc'

    name = fields.Char(u'单号')
    type = fields.Selection([('collection',u'收款'),('payment',u'付款')],u'收付款类型', default=lambda self:self._context.get('type'))
    user_id = fields.Many2one('res.users',u'申请人')
    contract_id = fields.Many2one('qdodoo.car.sale.contract',u'销售合同号')
    purchase_id = fields.Many2one('qdodoo.car.purchase.contract',u'外贸合同号')
    partner_id = fields.Many2one('res.partner',u'业务伙伴')
    bank_id = fields.Many2one('res.partner.bank',u'银行')
    bank_id_2 = fields.Many2one('res.partner.bank',u'银行')
    pay_project = fields.Many2one('qdodoo.car.expense',u'费用项目')
    pay_project_2 = fields.Many2one('qdodoo.car.expense',u'费用项目')
    # bank_num = fields.Char(related='bank_id.acc_number',string=u'银行账户')
    # bank_num_2 = fields.Char(related='bank_id_2.acc_number',string=u'银行账户')
    date_done = fields.Date(u'转账日期')
    all_money = fields.Float(u'金额',compute="_get_all_money")
    state = fields.Selection([('draft',u'草稿'),('pay',u'登账'),('done',u'完成'),('cancel',u'取消')],u'状态',default='draft')
    line = fields.One2many('qdodoo.car.payment.line','order_id',u'收款明细')
    is_pledge = fields.Boolean(u'是否是保证金',copy=False)
    is_bring = fields.Boolean(u'是否是赎车款',copy=False)
    is_tt = fields.Boolean(u'是否是tt',copy=False)
    margin_id = fields.Many2one('qdodoo.car.margin.money',u'二次保证金')
    carry_id = fields.Many2one('qdodoo.car.carry.money',u'提车款')
    issuing_id = fields.Many2one('qdodoo.car.issuing.manager',u'开证申请')
    bill_id = fields.Many2one('qdodoo.car.bill.lading',u'提单')
    expense_id = fields.Many2one('qdodoo.car.expense.in',u'费用录入')
    expense_id_car = fields.Many2one('qdodoo.car.expense.in',u'费用录入(按车)')
    company_partner = fields.Many2one('res.partner',u'公司对应的业务伙伴', default=lambda self:self.env['res.users'].browse(self._uid).company_id.partner_id)

    # 获取总金额
    def _get_all_money(self):
        for ids in self:
            ids.all_money = 0
            for line in ids.line:
                ids.all_money += line.money

    # 支付完成：1.更新销售订单中已收保证金字段
    @api.multi
    def write(self, vals):
        if vals.get('state') == 'done':
            if self.contract_id:
                self.contract_id.write({'is_issuing':True})
            if self.expense_id:
                self.expense_id.write({'state':'done'})
            if self.contract_id and self.is_pledge:
                for line in self.line:
                    line.product_num.write({'pledge_money':line.money,'all_car_money':line.product_num.all_car_money+line.money})
            if self.margin_id:
                for line in self.line:
                    line.product_num.write({'margin_id':self.margin_id.id,'margin_money':line.money,'all_car_money':line.product_num.all_car_money+line.money})
            if self.issuing_id:
                for line in self.line:
                    line.product_num.write({'invoice_issuing_money':line.money})
            if self.carry_id:
                for line in self.line:
                    line.product_num.write({'carry_money':line.money})
        return super(qdodoo_car_payment_order, self).write(vals)

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].get('qdodoo.car.payment.order')
        return super(qdodoo_car_payment_order, self).create(vals)

    # 确认
    @api.one
    def btn_pay(self):
        return self.write({'state':'pay'})

    # 取消
    @api.one
    def btn_cancel(self):
        return self.write({'state':'cancel'})

    # 完成
    @api.one
    def btn_done(self):
        if not self.date_done:
            raise osv.except_osv(_(u'警告'),_(u'请输入转账日期！'))
        if self.type == 'collection' and not self.bank_id:
            raise osv.except_osv(_(u'警告'),_(u'请输入银行！'))
        if self.type == 'payment' and not self.bank_id_2:
            raise osv.except_osv(_(u'警告'),_(u'请输入银行！'))
        return self.write({'state':'done'})

    # 返回
    @api.one
    def btn_draft(self):
        return self.write({'state':'draft'})

class qdodoo_car_payment_line(models.Model):
    _name = 'qdodoo.car.payment.line'

    order_id = fields.Many2one('qdodoo.car.payment.order',u'收款单')
    product_num = fields.Many2one('qdodoo.car.information',u'车架号')
    product_name = fields.Many2one('product.product',related='product_num.product_id',string=u'车辆型号')
    money = fields.Float(u'金额')