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

class qdodoo_car_margin_money(models.Model):
    """
        二次保证金
    """
    _name = 'qdodoo.car.margin.money'
    _order = 'id desc'

    name = fields.Char(u'编号')
    partner_id = fields.Many2one('res.partner',u'客户', required=True, default=lambda self:self._context.get('partner_id',''))
    state = fields.Selection([('draft',u'草稿'),('doing',u'收款通知'),('done',u'完成'),('cancel',u'取消'),('no_normal',u'异常')],u'状态',default='draft')
    order_line = fields.One2many('qdodoo.car.margin.money.line','margin_id',u'车辆明细')
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
            vals['name'] = self.env['ir.sequence'].get('qdodoo.car.margin.money')
        return super(qdodoo_car_margin_money, self).create(vals)

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
        value = {'type':'collection','margin_id':self.id,'partner_id':self.partner_id.id,'is_pledge':True}
        # 二次保证金
        model_id, pay_project= self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade','qdodoo_car_expense_2')
        value['pay_project'] = pay_project
        # 判断是否存在收款通知
        payment_id = payment_obj.search([('margin_id','=',self.id),('state','!=','cancel')])
        if not payment_id:
            # 创建对应的收款通知
            payment_id = payment_obj.create(value)
            # 创建对应的收款明细
            for line in self.order_line:
                line_obj.create({'order_id':payment_id.id,'product_num':line.product_num.id,'money':line.margin_money})
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

class qdodoo_car_margin_money_line(models.Model):
    _name = 'qdodoo.car.margin.money.line'

    margin_id = fields.Many2one('qdodoo.car.margin.money',u'二次保证金')
    product_num = fields.Many2one('qdodoo.car.information',u'车架号')
    product_id = fields.Many2one('product.product',u'车辆型号', related="product_num.product_id")
    price_unit = fields.Float(u'销售合同价', related="product_num.price_unit")
    all_car_money = fields.Float(u'预收款', related="product_num.all_car_money")
    margin_money = fields.Float(u'二次保证金金额')