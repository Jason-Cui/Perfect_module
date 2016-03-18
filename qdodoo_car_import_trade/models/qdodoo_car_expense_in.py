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

class qdodoo_car_expense_in(models.Model):
    """
        费用登录
    """
    _name = 'qdodoo.car.expense.in'
    _order = 'id desc'

    name = fields.Char(u'单号')
    purchase_id = fields.Many2one('qdodoo.car.purchase.contract',u'外贸合同号')
    partner_id = fields.Many2one('res.partner',u'供应商', related="purchase_id.partner_id")
    partner_num = fields.Char(u'供应商单号')
    currency_id = fields.Many2one('res.currency',u'币种',default=lambda self:self.env['res.users'].browse(self._uid).company_id.currency_id)
    date_order = fields.Date(u'发生日期')
    expense_id = fields.Many2one('qdodoo.car.expense',u'费用项目')
    order_line = fields.One2many('qdodoo.car.expense.in.line','expense_id',u'车辆明细')
    state = fields.Selection([('draft',u'草稿'),('doing',u'付款'),('done',u'完成'),('cancel',u'取消')],u'状态',default='draft')
    all_total = fields.Float(u'总金额',compute="_get_money")

    def _get_money(self):
        for ids in self:
            ids.all_total = 0
            for line in ids.order_line:
                ids.all_total += line.tax_money

    # 获取唯一的编号
    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].get('qdodoo.car.expense.in')
        return super(qdodoo_car_expense_in, self).create(vals)

    # 确认
    @api.one
    def btn_doing(self):
        if not self.all_total:
            raise osv.except_osv(_(u'警告'),_(u'录入的费用金额为0！'))
        return self.write({'state':'doing'})

    # 取消
    @api.one
    def btn_cancel(self):
        return self.write({'state':'cancel'})

    # 付款
    @api.multi
    def btn_payment(self):
        payment_obj = self.env['qdodoo.car.payment.order']
        line_obj = self.env['qdodoo.car.payment.line']
        domain = [('type','=','payment'),('expense_id','=',self.id),('state','!=','cancel')]
        value = {'type':'payment','expense_id':self.id,'partner_id':self.partner_id.id}
        value['pay_project_2'] = self.expense_id.id
        # 判断是否存在收款通知
        payment_id = payment_obj.search(domain)
        if not payment_id:
            # 创建对应的付款申请
            payment_id = payment_obj.create(value)
            # 创建对应的收款明细
            # 获取外贸合同对应的车辆档案
            for line in self.order_line:
                line_obj.create({'order_id':payment_id.id,'product_num':line.product_num.id,'money':line.product_price})
        result = self.env['ir.model.data'].get_object_reference( 'qdodoo_car_import_trade', 'tree_qdodoo_car_payment_order')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'form_qdodoo_car_payment_order')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('付款申请'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.payment.order',
              'type': 'ir.actions.act_window',
              'domain':[('id','=',payment_id.id)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

    # 驳回
    @api.one
    def btn_return(self):
        return self.write({'state':'draft'})

class qdodoo_car_expense_in_line(models.Model):
    """
        费用登录明细
    """
    _name = 'qdodoo.car.expense.in.line'

    expense_id = fields.Many2one('qdodoo.car.expense.in',u'费用登录')
    product_num = fields.Many2one('qdodoo.car.information',u'车架号')
    product_id = fields.Many2one('product.product',u'车辆型号',related="product_num.product_id")
    tax_rate = fields.Float(u'税金比例(%)')
    tax_money = fields.Float(u'含税价', compute='_get_tax_money')
    product_price = fields.Float(u'不含税价')

    # 计算含税价
    def _get_tax_money(self):
        for ids in self:
            if ids.product_price:
                ids.tax_money = ids.product_price * (1 + ids.tax_rate/100)

class qdodoo_car_expense_in_car(models.Model):
    """
        费用登录-按车
    """
    _name = 'qdodoo.car.expense.in.car'
    _order = 'id desc'

    name = fields.Char(u'单号')
    expense_id = fields.Many2one('qdodoo.car.information',u'车辆')
    purchase_id = fields.Many2one('qdodoo.car.purchase.contract',u'外贸合同号', related="expense_id.purchase_id")
    partner_id = fields.Many2one('res.partner',u'供应商', related="purchase_id.partner_id")
    partner_num = fields.Char(u'供应商单号')
    currency_id = fields.Many2one('res.currency',u'币种',default=lambda self:self.env['res.users'].browse(self._uid).company_id.currency_id)
    date_order = fields.Date(u'发生日期')
    order_line = fields.One2many('qdodoo.car.expense.in.car.line','expense_id',u'费用明细')
    state = fields.Selection([('draft',u'草稿'),('doing',u'付款'),('done',u'完成'),('cancel',u'取消')],u'状态',default='draft')
    all_total = fields.Float(u'总金额',compute="_get_money")

    # 计算总金额
    def _get_money(self):
        for ids in self:
            ids.all_total = 0
            for line in ids.order_line:
                ids.all_total += line.product_price

    # 获取明细数据
    @api.onchange('expense_id')
    def _get_order_line(self):
        self.order_line = ''
        line = []
        for line_obj in self.env['qdodoo.car.expense'].search([('expense_type','=','receivable')]):
            line.append((0,0,{'product_num':line_obj.id}))
        self.order_line = line

    # 获取唯一的编号
    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].get('qdodoo.car.expense.in')
        return super(qdodoo_car_expense_in_car, self).create(vals)

    # 确认
    @api.one
    def btn_doing(self):
        if not self.all_total:
            raise osv.except_osv(_(u'警告'),_(u'录入的费用金额为0！'))
        return self.write({'state':'doing'})

    # 取消
    @api.one
    def btn_cancel(self):
        return self.write({'state':'cancel'})

    # 付款
    @api.one
    def btn_payment(self):
        payment_obj = self.env['qdodoo.car.payment.order']
        line_obj = self.env['qdodoo.car.payment.line']
        domain = [('type','=','payment'),('expense_id_car','=',self.id),('state','!=','cancel')]
        value = {'type':'payment','expense_id_car':self.id,'partner_id':self.partner_id.id}
        # 判断是否存在收款通知
        payment_id = payment_obj.search(domain)
        if not payment_id:
            # 创建对应的付款申请
            payment_id = payment_obj.create(value)
            # 创建对应的收款明细
            # 获取外贸合同对应的车辆档案
            for line in self.order_line:
                line_obj.create({'order_id':payment_id.id,'product_num':line.product_num.id,'money':line.product_price})
        result = self.env['ir.model.data'].get_object_reference( 'qdodoo_car_import_trade', 'tree_qdodoo_car_payment_order')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'form_qdodoo_car_payment_order')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('付款申请'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.payment.order',
              'type': 'ir.actions.act_window',
              'domain':[('id','=',payment_id.id)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

    # 驳回
    @api.one
    def btn_return(self):
        return self.write({'state':'draft'})

class qdodoo_car_expense_in_car_line(models.Model):
    """
        费用登录明细
    """
    _name = 'qdodoo.car.expense.in.car.line'

    expense_id = fields.Many2one('qdodoo.car.expense.in.car',u'费用登录')
    product_num = fields.Many2one('qdodoo.car.expense',u'费用项目')
    product_price = fields.Float(u'单价')
