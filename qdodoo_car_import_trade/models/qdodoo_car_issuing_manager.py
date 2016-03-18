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

class qdodoo_car_issuing_manager(models.Model):
    """
        开证
    """
    _name = 'qdodoo.car.issuing.manager'
    _rec_name = 'issuing_num'
    _order = 'id desc'

    name = fields.Char(u'开证申请编号')
    purchase_id = fields.Many2one('qdodoo.car.purchase.contract',u'外贸合同号', required=True)
    partner_id = fields.Many2one('res.partner',u'供应商', related="purchase_id.partner_id")
    issuing_date = fields.Date(u'申请日期')
    issuing_money = fields.Float(u'开证金额', compute="_get_issuing_money")
    state = fields.Selection([('draft',u'草稿'),('doing',u'付款'),('done',u'完成'),('cancel',u'取消')],u'状态',default="draft")
    issuing_num = fields.Char(u'信用证编号')
    issuing_type = fields.Selection([('near',u'即期'),('long',u'90天远期')],u'信用证类型')
    partner_address = fields.Char(u'供应商地址', related="purchase_id.partner_id.street")
    partner_bank = fields.Many2one('res.partner.bank',u'供应商银行')
    bank_account = fields.Char(u'银行账户', related="partner_bank.acc_number")
    bank_address = fields.Char(u'银行地址', related="partner_bank.street")
    swifi_code = fields.Char(u'SWIFT Code', related="partner_bank.bank_bic")
    currency_id = fields.Many2one('res.currency',u'货币', related="purchase_id.currency_id")
    order_line = fields.One2many('qdodoo.car.purchase.contract.line','issuing_id',u'车辆明细')
    payment_type = fields.Char(u'付款方式')
    payment_rate = fields.Float(u'付款比例')
    issuing_payment_rate = fields.Float(u'开证保证金比例',default='100')
    buy_rate = fields.Float(u'购汇汇率',digits=(14,6))
    issuing_pay_rate = fields.Float(u'开证保证金汇率',digits=(14,6))
    bank_partner = fields.Many2one('res.partner',u'开证行')
    type = fields.Selection([('issuing',u'信用证'),('tt',u'TT')],u'类型',default=lambda self:self._context.get('type'))

    # 计算开证金额
    def _get_issuing_money(self):
        for ids in self:
            ids.issuing_money = 0
            for line in ids.order_line:
                ids.issuing_money += line.all_money

    # 只能删除草稿或取消的订单
    @api.multi
    def unlink(self):
        for ids in self:
            if ids.state not in ('draft','cancel'):
                raise osv.except_osv(_(u'错误'),_(u'只能删除草稿或取消的订单！'))
        return super(qdodoo_car_issuing_manager, self).unlink()

    # 获取唯一的编号
    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].get('qdodoo.car.issuing.manager')
        res_id = super(qdodoo_car_issuing_manager, self).create(vals)
        if vals.get('purchase_id'):
            self.env['qdodoo.car.purchase.contract'].write({'issuing_id':res_id.id})
        return res_id

    # 确认(更新车辆档案中关于开证的字段,外贸合同中的关联字段)
    @api.one
    def btn_doing(self):
        car_obj = self.env['qdodoo.car.information']
        for line in self.order_line:
            # 查询满足条件的车辆档案
            for count in range(line.product_qty):
                car_ids = car_obj.search([('purchase_id','=',self.purchase_id.id),('product_id','=',line.product_id.id),('issuing_id','=',False)])
                if car_ids:
                    car_ids[0].write({'issuing_id':self.id,'issuing_money':line.price_unit,'issuing_type':self.issuing_type,'issuing_date':self.issuing_date})
                else:
                    raise osv.except_osv(_('错误!'), _('车辆档案数据异常.'))
        self.purchase_id.write({'issuing_id':self.id})
        return self.write({'state':'doing'})

    # 取消
    @api.one
    def btn_cancel(self):
        self.purchase_id.write({'issuing_id':''})
        return self.write({'state':'cancel'})

    # 保证金
    @api.multi
    def btn_payment(self):
        payment_obj = self.env['qdodoo.car.payment.order']
        line_obj = self.env['qdodoo.car.payment.line']
        information_obj = self.env['qdodoo.car.information']
        domain = [('type','=','payment'),('is_tt','=',False),('issuing_id','=',self.id),('state','!=','cancel')]
        value = {'type':'payment','issuing_id':self.id,'partner_id':self.bank_partner.id}
        # 是保证金
        model_id, pay_project= self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade','qdodoo_car_expense_5')
        value['pay_project_2'] = pay_project
        # 判断是否存在收款通知
        payment_id = payment_obj.search(domain)
        if not payment_id:
            # 创建对应的付款申请
            payment_id = payment_obj.create(value)
            # 创建对应的收款明细
            # 获取外贸合同对应的车辆档案
            for line in self.order_line:
                information_ids = information_obj.search([('issuing_money','=',line.price_unit),('purchase_id','=',self.purchase_id.id),('product_id','=',line.product_id.id)])
                for information_id in information_ids:
                    line_obj.create({'order_id':payment_id.id,'product_num':information_id.id,'money':line.price_unit*self.issuing_payment_rate/100*self.issuing_pay_rate})
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

    # 付款
    @api.multi
    def btn_payment_money(self):
        payment_obj = self.env['qdodoo.car.payment.order']
        line_obj = self.env['qdodoo.car.payment.line']
        information_obj = self.env['qdodoo.car.information']
        domain = [('type','=','payment'),('is_tt','=',True),('purchase_id','=',self.purchase_id.id),('state','!=','cancel')]
        value = {'type':'payment','is_tt':True,'purchase_id':self.purchase_id.id,'partner_id':self.partner_id.id}
        # 是保证金
        model_id, pay_project= self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade','qdodoo_car_expense_4')
        value['pay_project_2'] = pay_project
        # 判断是否存在付款申请
        payment_id = payment_obj.search(domain)
        if not payment_id:
            # 创建对应的付款申请
            payment_id = payment_obj.create(value)
            # 创建对应的收款明细
            # 获取外贸合同对应的车辆档案
            for line in self.order_line:
                information_ids = information_obj.search([('purchase_id','=',self.purchase_id.id),('product_id','=',line.product_id.id)])
                for information_id in information_ids:
                    line_obj.create({'order_id':payment_id.id,'product_num':information_id.id,'money':line.price_unit*self.payment_rate/100*self.buy_rate})
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

    # 完成
    @api.one
    def btn_done(self):
        return self.write({'state':'done'})

    # 结汇(提单列表)
    @api.multi
    def btn_negotiation(self):
        bill_obj = self.env['qdodoo.car.bill.lading']
        res_id = bill_obj.search([('purchase_id','=',self.purchase_id.id)])
        result = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'view_tree_qdodoo_car_bill_lading')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'view_form_qdodoo_car_bill_lading')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('提单'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.bill.lading',
              'type': 'ir.actions.act_window',
              'domain':[('id','in',res_id.ids)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

    # 结汇完成
    @api.one
    def btn_negotiation_done(self):
        information_obj = self.env['qdodoo.car.information']
        for line in self.order_line:
            information_ids = information_obj.search([('purchase_id','=',self.purchase_id.id),('product_id','=',line.product_id.id)])
            information_ids.write({'issuing_money':line.price_unit})
        return self.write({'state':'done'})
