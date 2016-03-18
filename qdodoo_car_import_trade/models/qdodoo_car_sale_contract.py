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

class qdodoo_car_sale_contract(models.Model):
    """
        销售合同
    """
    _name = 'qdodoo.car.sale.contract'
    _rec_name = 'contract_num'
    _order = 'id desc'

    name = fields.Char(u'合同编号')
    contract_num = fields.Char(u'合同号', required=True, default=lambda self:str(datetime.now().year)+'-SDHSLGXHSC-')
    partner_id = fields.Many2one('res.partner',u'客户', required=True)
    date_order = fields.Date(u'合同日期', required=True, default=datetime.now().date())
    car_number = fields.Float(u'车辆数',compute="_get_car_number")
    amount_total = fields.Float(u'金额',compute="_get_car_number")
    deposit_rate = fields.Float(u'保证金比例(%)', required=True)
    state = fields.Selection([('draft',u'草稿'),('doing',u'执行'),('done',u'完成'),('cancel',u'取消'),('no_normal',u'异常')],u'状态',default='draft')
    order_line = fields.One2many('qdodoo.car.sale.contract.line','order_id',u'车辆明细')
    file_name = fields.Char(u'合同名称', copy=False)
    contract_file = fields.Binary(u'合同扫描件', copy=False)
    pledge_money = fields.Float(u'保证金已收金额', copy=False)
    currency_id = fields.Many2one('res.currency',u'外币币种', required=True)
    currency_raise = fields.Float(u'外币汇率', required=True, digits=(14,6))
    is_issuing = fields.Boolean(u'已收保证金',copy=False)
    is_make_invoice = fields.Boolean(u'全部已开票',copy=False)
    is_payment = fields.Boolean(u'全部已收提车款',copy=False)
    is_settlement = fields.Boolean(u'已结算',copy=False)
    dalay_date = fields.Float(u'延期天数', default='90')
    dalay_rate = fields.Float(u'押汇利率(%)', default='4.5')
    dalay_china_rate = fields.Float(u'延期利率(%)人民币', default='10')

    _sql_constraints = [
        ('contract_num_uniq', 'unique(contract_num)',
            '销售合同号已存在!'),
    ]

    @api.onchange('currency_id')
    def onchange_currcency(self):
        if self.currency_id:
            self.currency_raise = 1/self.currency_id.rate_silent

    # 只能删除草稿或取消的订单
    @api.multi
    def unlink(self):
        for ids in self:
            if ids.state not in ('draft','cancel'):
                raise osv.except_osv(_(u'错误'),_(u'只能删除草稿或取消的订单！'))
        return super(qdodoo_car_sale_contract, self).unlink()

    # 获取唯一的编号
    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].get('qdodoo.car.sale.contract')
        return super(qdodoo_car_sale_contract, self).create(vals)

    # 获取车辆数量、金额
    def _get_car_number(self):
        for ids in self:
            number = 0
            money = 0
            for line in ids.order_line:
                number += line.product_qty
                money += line.all_money
            ids.car_number = number
            ids.amount_total = money

    # 押汇申请（销售）
    @api.multi
    def btn_negotiation_sale(self):
        negotiation_obj = self.env['qdodoo.car.negotiation.manager.sale']
        # 判断是否存在押汇
        negotiation_id = negotiation_obj.search([('purchase_id.contract_id','=',self.id),('state','!=','cancel')])
        result = self.env['ir.model.data'].get_object_reference( 'qdodoo_car_import_trade', 'tree_qdodoo_car_negotiation_manager_sale')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'form_qdodoo_car_negotiation_manager_sale')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('押汇'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.negotiation.manager.sale',
              'type': 'ir.actions.act_window',
              'domain':[('id','=',negotiation_id.ids)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

    @api.one
    # 确认销售合同(生成车辆档案)
    def btn_doing(self):
        information_obj = self.env['qdodoo.car.information']
        for ids in self:
            if not ids.order_line:
                raise osv.except_osv(_('错误!'), _('请输入车辆明细.'))
            for line in ids.order_line:
                # 判断如果存在车架号，则数量只能为1
                if line.product_num and line.product_qty != 1:
                    raise osv.except_osv(_('错误!'), _('填写车架号的明细数量只能为1.'))
                line.write({'rest_qty':line.product_qty})
                val = {}
                val['sale_contract'] = ids.id
                val['product_id'] = line.product_id.id
                val['price_unit'] = line.price_unit
                val['tax_money'] = line.tax_money
                val['product_num'] = line.product_num
                val['pledge_money'] = line.pledge_money/line.product_qty
                val['agent_money'] = line.agent_money
                val['currency_id'] = self.currency_id.id
                if line.product_qty > 1:
                    for k in range(line.product_qty):
                        information_obj.create(val)
                else:
                    information_obj.create(val)
        return self.write({'state':'doing'})

    @api.multi
    # 保证金(收款通知)
    def btn_predict_money(self):
        payment_obj = self.env['qdodoo.car.payment.order']
        line_obj = self.env['qdodoo.car.payment.line']
        information_obj = self.env['qdodoo.car.information']
        domain = [('type','=','collection'),('contract_id','=',self.id),('is_pledge','=',True),('state','!=','cancel')]
        value = {'type':'collection','contract_id':self.id,'partner_id':self.partner_id.id,'is_pledge':True}
        # 是保证金
        model_id, pay_project= self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade','qdodoo_car_expense_1')
        value['pay_project'] = pay_project
        # 判断是否存在收款通知
        payment_id = payment_obj.search(domain)
        if not payment_id:
            # 创建对应的收款通知
            payment_id = payment_obj.create(value)
            # 创建对应的收款明细
            # 获取销售订单对应的车辆档案
            information_ids = information_obj.search([('sale_contract','=',self.id)])
            for information_id in information_ids:
                money =information_id.pledge_money
                line_obj.create({'order_id':payment_id.id,'product_num':information_id.id,'money':money})
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

    @api.multi
    # 二次保证金
    def btn_predict_money_two(self):
        margin_obj = self.env['qdodoo.car.margin.money']
        margin_ids = margin_obj.search([('partner_id','=',self.partner_id.id)])
        result = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'tree_qdodoo_car_margin_money')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'form_qdodoo_car_margin_money')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('二次保证金'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.margin.money',
              'type': 'ir.actions.act_window',
              'domain':[('id','=',margin_ids.ids)],
              'context':{'partner_id':self.partner_id.id},
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

    @api.multi
    # 提车款
    def btn_bring_car(self):
        carry_obj = self.env['qdodoo.car.carry.money']
        carry_ids = carry_obj.search([('partner_id','=',self.partner_id.id)])
        result = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'tree_qdodoo_car_carry_money')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'form_qdodoo_car_carry_money')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('提车款'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.carry.money',
              'type': 'ir.actions.act_window',
              'domain':[('id','=',carry_ids.ids)],
              'context':{'partner_id':self.partner_id.id},
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

    @api.multi
    # 结算
    def btn_squaring_up(self):
        settlement_obj = self.env['qdodoo.car.settlement']
        settlement_ids = settlement_obj.search([('sale_id','=',self.id)])
        result = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'tree_qdodoo_car_settlement')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'form_qdodoo_car_settlement')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('结算单'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.settlement',
              'type': 'ir.actions.act_window',
              'domain':[('id','=',settlement_ids.ids)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

    @api.one
    # 取消
    def btn_cancel(self):
        return self.write({'state':'cancel'})

    @api.one
    # 异常
    def btn_unusual(self):
        return self.write({'state':'no_normal'})

    @api.one
    # 恢复执行
    def btn_perform(self):
        return self.write({'state':'doing'})

    @api.multi
    # 查看车辆档案
    def btn_car_information(self):
        information_obj = self.env['qdodoo.car.information']
        information_ids = information_obj.search([('sale_contract','=',self.id)])
        result = self.env['ir.model.data'].get_object_reference( 'qdodoo_car_import_trade', 'tree_qdodoo_car_information')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'form_qdodoo_car_information')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('车辆档案'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.information',
              'type': 'ir.actions.act_window',
              'domain':[('id','in',information_ids.ids)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

    @api.multi
    # 查看外贸合同
    def btn_purchase_contract(self):
        purchase_obj = self.env['qdodoo.car.purchase.contract']
        purchase_ids = purchase_obj.search([('contract_id','=',self.id)])
        result = self.env['ir.model.data'].get_object_reference( 'qdodoo_car_import_trade', 'tree_qdodoo_car_purchase_contract')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'form_qdodoo_car_purchase_contract')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('外贸合同'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.purchase.contract',
              'type': 'ir.actions.act_window',
              'domain':[('id','in',purchase_ids.ids)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

class qdodoo_car_sale_contract_line(models.Model):
    """
        销售合同车辆明细
    """
    _name = 'qdodoo.car.sale.contract.line'

    order_id = fields.Many2one('qdodoo.car.sale.contract',u'销售合同')
    product_id = fields.Many2one('product.product',u'车辆型号', required=True)
    price_unit = fields.Float(u'单车车价(外币)', required=True)
    tax_money = fields.Float(u'单车税费', required=True)
    product_qty = fields.Integer(u'数量', required=True)
    rest_qty = fields.Integer(u'没有外贸合同的数量')
    all_money = fields.Float(u'总价款',compute="_get_all_money")
    pledge_money = fields.Float(u'保证金金额合计', compute="_get_all_money")
    agent_money = fields.Float(u'单车平台费', required=True)
    # agent_all = fields.Float(u'平台费合计',compute="_get_agent_all")
    product_num = fields.Char(u'车架号')

    @api.onchange('product_id')
    def _onchange_line(self):
        if not self.order_id.currency_raise:
            raise osv.except_osv(_('警告!'),_("外币汇率不能为空！"))

    # 计算总价款
    def _get_all_money(self):
        for ids in self:
            ids.all_money = (ids.price_unit*ids.order_id.currency_raise + ids.tax_money) * ids.product_qty
            ids.pledge_money = ids.price_unit * ids.order_id.currency_raise * ids.product_qty * ids.order_id.deposit_rate / 100

    # 平台费合计
    # def _get_agent_all(self):
    #     for ids in self:
    #         ids.agent_all = ids.agent_money * ids.product_qty

class qdodoo_open_invoice_line(models.TransientModel):
    """
        开票明细选择
    """
    _name = 'qdodoo.open.invoice.line'

    order_id = fields.Many2one('qdodoo.car.sale.contract',u'销售订单', default=lambda self:self._context.get('active_id'))
    line = fields.Many2many('qdodoo.car.information','qdodoo_open_invoice_info_rel','wizard_id','line_id', string="开票的车辆明细")

    @api.multi
    # 创建/查看开票申请
    def btn_create_invoice(self):
        order_id = self._context.get('active_id')
        contract_obj = self.env['qdodoo.car.sale.contract']
        invoice_obj = self.env['qdodoo.car.make.invoice']
        is_create = self._context.get('create')
        if is_create:
            sale_contract = contract_obj.browse(order_id)
            res_id = invoice_obj.create({'contract_id':order_id,'invoice_type':'add_tax','partner_id':sale_contract.partner_id.id,
                                     'date':datetime.now().date()})
            # 创建开票明细
            for line in self.line:
                line.write({'make_invoice':res_id.id})
        else:
            # 查询已有的开票申请
            res_id = invoice_obj.search([('contract_id','=',order_id)])
        result = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'tree_qdodoo_car_make_invoice')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'form_qdodoo_car_make_invoice')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('开票申请'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.make.invoice',
              'type': 'ir.actions.act_window',
              'domain':[('id','in',res_id.ids)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }