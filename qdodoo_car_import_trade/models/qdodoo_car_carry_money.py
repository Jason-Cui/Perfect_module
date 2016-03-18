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

class qdodoo_car_carry_money(models.Model):
    """
        提车款
    """
    _name = 'qdodoo.car.carry.money'
    _order = 'id desc'

    name = fields.Char(u'编号')
    partner_id = fields.Many2one('res.partner',u'客户', required=True, default=lambda self:self._context.get('partner_id',''))
    state = fields.Selection([('draft',u'草稿'),('doing',u'收款通知'),('done',u'完成'),('cancel',u'取消'),('no_normal',u'异常')],u'状态',default='draft')
    order_line = fields.One2many('qdodoo.car.carry.money.line','carry_id',u'车辆明细')
    car_number = fields.Float(u'车辆数',compute="_get_car_number")

    # 计算车辆数
    def _get_car_number(self):
        for ids in self:
            ids.car_number = 0
            for line in ids.order_line:
                ids.car_number += 1

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].get('qdodoo.car.carry.money')
        return super(qdodoo_car_carry_money, self).create(vals)

    # 确认
    @api.one
    def btn_doing(self):
        return self.write({'state':'doing'})

    # 取消
    @api.one
    def btn_cancel(self):
        return self.write({'state':'cancel'})

    # 驳回
    @api.one
    def btn_draft(self):
        return self.write({'state':'draft'})

    # 收款通知
    @api.multi
    def btn_payment(self):
        payment_obj = self.env['qdodoo.car.payment.order']
        line_obj = self.env['qdodoo.car.payment.line']
        value = {'type':'collection','carry_id':self.id,'partner_id':self.partner_id.id}
        # 提车款
        model_id, pay_project= self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade','qdodoo_car_expense_3')
        value['pay_project'] = pay_project
        # 判断是否存在收款通知
        payment_id = payment_obj.search([('carry_id','=',self.id),('state','!=','cancel')])
        if not payment_id:
            # 创建对应的收款通知
            payment_id = payment_obj.create(value)
            # 创建对应的收款明细
            for line in self.order_line:
                if not line.estimate_money:
                    raise osv.except_osv(_(u'警告'),_(u'请输入预估车款估值！'))
                line_obj.create({'order_id':payment_id.id,'product_num':line.product_num.id,'money':line.subtitle})
        result = self.env['ir.model.data'].get_object_reference( 'qdodoo_car_import_trade', 'tree_qdodoo_car_payment_order')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'form_qdodoo_car_payment_order')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('收款通知'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.payment.order',
              'type': 'ir.actions.act_window',
              'domain':[('id','=',payment_id.id)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

class qdodoo_car_carry_money_line(models.Model):
    """
        提车款明细
    """
    _name = 'qdodoo.car.carry.money.line'

    carry_id = fields.Many2one('qdodoo.car.carry.money',u'提车款')
    product_num = fields.Many2one('qdodoo.car.information',u'车架号')
    product_id = fields.Many2one('product.product',u'车辆型号', related="product_num.product_id")
    # purchase_id = fields.Many2one('qdodoo.car.purchase.contract',u'外贸合同号', related="product_num.purchase_id")
    sale_price = fields.Float(u'进口裸车价', related="product_num.sale_price")
    in_tax = fields.Float(u'进口关税', related="product_num.in_tax")
    in_sale_tax = fields.Float(u'进口消费税', related="product_num.in_sale_tax")
    add_tax = fields.Float(u'进口增值税', related="product_num.add_tax")
    pad_interest = fields.Float(u'垫税利息', related="product_num.pad_interest")
    negotiation_sale_interest = fields.Float(u'押汇利息', related="product_num.negotiation_sale_interest")
    clearance_money = fields.Float(u'清关费用', related="product_num.clearance_money")
    all_issure = fields.Float(u'保险费', related="product_num.all_issure")
    # bank_money = fields.Float(u'银行手续费', related="product_num.all_issure")
    logistics_money = fields.Float(u'物流费用', related="product_num.logistics_money")
    # tax_price = fields.Float(u'开票价格', related="product_num.tax_price")
    # pad_tax_money = fields.Float(u'开票费用', related="product_num.pad_tax_money")
    invoice_issuing_money = fields.Float(u'开证保证金', related="product_num.invoice_issuing_money")
    other_issuing_money = fields.Float(u'其他保证金', related="product_num.other_issuing_money")
    delayed_moeny = fields.Float(u'滞报金', related="product_num.delayed_moeny")
    in_issuing_money = fields.Float(u'海关保证金', related="product_num.in_issuing_money")
    subtitle = fields.Float(u'合计', compute="_get_subtitle")
    estimate_money = fields.Float(u'预估车款估值')

    def _get_subtitle(self):
        for ids in self:
            ids.subtitle = ids.purchase_price+ids.in_tax+ids.in_sale_tax+ids.add_tax+ids.pad_interest+ids.negotiation_sale_interest+ids.clearance_money+ids.all_issure+ids.in_issuing_money+ids.logistics_money+ids.in_issuing_money - ids.invoice_issuing_money - ids.other_issuing_money
