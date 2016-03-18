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

class qdodoo_car_purchase_contract(models.Model):
    """
        外贸合同
    """
    _name = 'qdodoo.car.purchase.contract'
    _rec_name = 'contract_num'
    _order = 'id desc'

    name = fields.Char(u'合同编号')
    contract_num = fields.Char(u'外贸合同号',required=True)
    contract_id = fields.Many2one('qdodoo.car.sale.contract',u'销售合同号',required=True, domain=[('state','=','doing')])
    date_order = fields.Date(u'合同日期',required=True)
    partner_id = fields.Many2one('res.partner',u'供应商',required=True)
    customer_id = fields.Many2one('res.partner',related='contract_id.partner_id', string='客户')
    date_ship = fields.Date(u'最迟装船日期')
    car_number = fields.Float(u'车辆数',compute="_get_car_number")
    amount_total = fields.Float(u'金额',compute="_get_car_number")
    state = fields.Selection([('draft',u'草稿'),('doing',u'执行'),('done',u'完成'),('cancel',u'取消'),('unusual',u'异常')],u'状态',default='draft')
    currency_id = fields.Many2one('res.currency',u'货币',required=True)
    out_port = fields.Many2one('qdodoo.car.port.manager',u'发货港',domain=[('type','=','out')],required=True)
    in_port = fields.Many2one('qdodoo.car.port.manager',u'到货港',domain=[('type','=','in')],required=True)
    pack_type = fields.Selection([('box',u'集装箱')],u'包装',required=True)
    price_term = fields.Selection([('ctr','CFR'),('fob','FOB')],u'价格术语',required=True)
    order_line = fields.One2many('qdodoo.car.purchase.contract.line','purchase_id',u'车辆明细')
    payment_type = fields.Many2one('qdodoo.car.payment.type',u'付款方式',required=True)
    issuing_id = fields.Many2one('qdodoo.car.issuing.manager',u'开证申请')
    is_issuing = fields.Boolean(u'已开证',copy=False)
    is_negotiation = fields.Boolean(u'已押汇',copy=False)
    is_negotiation_end = fields.Boolean(u'已结汇',copy=False)
    is_bill = fields.Boolean(u'全部已收提单',copy=False)
    is_tax = fields.Boolean(u'垫税中',copy=False)
    is_settlement = fields.Boolean(u'已结算',copy=False)
    is_bill_new = fields.Boolean(u'已有提单',copy=False)

    _sql_constraints = [
        ('contract_num_uniq', 'unique(contract_num)',
            '外贸合同号已存在!'),
    ]

    # 只能删除草稿或取消的订单
    @api.multi
    def unlink(self):
        for ids in self:
            if ids.state not in ('draft','cancel'):
                raise osv.except_osv(_(u'错误'),_(u'只能删除草稿或取消的订单！'))
        return super(qdodoo_car_purchase_contract, self).unlink()

    # 选择销售合同，自动关联出对应的明细、货币
    @api.onchange('contract_id')
    def _onchange_line(self):
        self.order_line = ''
        order_line = []
        for line in self.contract_id.order_line:
            if line.rest_qty > 0:
                order_line.append((0, 0, {'product_id':line.product_id.id,'product_qty':line.rest_qty,'price_unit':line.price_unit,'sale_line':line.id}))
        self.order_line = order_line
        self.currency_id = self.contract_id.currency_id.id

    # 获取唯一的编号
    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].get('qdodoo.car.purchase.contract')
        return super(qdodoo_car_purchase_contract, self).create(vals)

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

    @api.multi
    # 查看车辆档案
    def btn_car_information(self):
        information_obj = self.env['qdodoo.car.information']
        information_ids = information_obj.search([('purchase_id','=',self.id)])
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

    @api.one
    # 取消
    def btn_cancel(self):
        return self.write({'state':'cancel'})

    @api.one
    # 异常
    def btn_unusual(self):
        return self.write({'state':'unusual'})

    @api.one
    # 恢复异常
    def btn_perform(self):
        return self.write({'state':'doing'})

    @api.one
    # 确认（校验数量是否超过了销售合同中的数量,销售合同明细中可选择数量减少，车辆档案中关联对应的外贸合同、币种、金额等信息）
    def btn_doing(self):
        car_information = self.env['qdodoo.car.information']
        for ids in self:
            if not ids.order_line:
                raise osv.except_osv(_('错误!'), _('请输入车辆明细.'))
            else:
                for line in ids.order_line:
                    if line.product_qty > line.sale_line.rest_qty:
                        raise osv.except_osv(_('错误!'), _('车辆明细中产品数量超过了销售合同中未签订外贸合同的产品数量.'))
                    else:
                        line.sale_line.write({'rest_qty':line.sale_line.rest_qty-line.product_qty})
                    for count in range(line.product_qty):
                        car_id = car_information.search([('sale_contract','=',self.contract_id.id),('product_id','=',line.product_id.id),('purchase_id','=',False)])
                        if car_id:
                            car_id[0].write({'purchase_id':self.id,'purchase_currency_id':self.currency_id.id,'purchase_date':self.date_order,'purchase_price':line.price_unit})
                        else:
                            raise osv.except_osv(_('错误!'), _('车辆档案数据异常.'))
        return self.write({'state':'doing'})

    @api.multi
    # 开证
    def btn_issuing(self):
        issuing_obj = self.env['qdodoo.car.issuing.manager']
        # 判断是否存在开证申请
        issuing_id = issuing_obj.search([('type','=','issuing'),('purchase_id','=',self.id),('state','!=','cancel')])
        if not issuing_id:
            # 创建对应的开证申请
            value = {}
            value['purchase_id'] = self.id
            value['issuing_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            value['payment_type'] = self.payment_type.name
            value['type'] = 'issuing'
            issuing_id = issuing_obj.create(value)
            # 创建对应的明细
            for line in self.order_line:
                line.write({'issuing_id':issuing_id.id})
        result = self.env['ir.model.data'].get_object_reference( 'qdodoo_car_import_trade', 'tree_qdodoo_car_issuing_manager')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'form_qdodoo_car_issuing_manager')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('开证'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.issuing.manager',
              'type': 'ir.actions.act_window',
              'domain':[('id','=',issuing_id.id)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

    @api.multi
    # 押汇
    def btn_negotiation(self):
        negotiation_obj = self.env['qdodoo.car.negotiation.manager']
        issuing_obj = self.env['qdodoo.car.issuing.manager']
        # 判断是否存在押汇
        negotiation_id = negotiation_obj.search([('purchase_id','=',self.id),('state','!=','cancel')])
        if not negotiation_id:
            # 判断是否已存在确认的开证申请
            issuing_ids = issuing_obj.search([('purchase_id','=',self.id),('state','in',('doing','done'))])
            if not issuing_ids:
                raise osv.except_osv(_(u'错误'),_(u'不存在确认的开证申请，请先创建或确认开证申请！'))
            # 创建对应的押汇
            value = {}
            value['purchase_id'] = self.id
            negotiation_id = negotiation_obj.create(value)
        result = self.env['ir.model.data'].get_object_reference( 'qdodoo_car_import_trade', 'tree_qdodoo_car_negotiation_manager')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'form_qdodoo_car_negotiation_manager')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('押汇'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.negotiation.manager',
              'type': 'ir.actions.act_window',
              'domain':[('id','=',negotiation_id.id)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

    @api.multi
    # 垫税
    def btn_pad_tax(self):
        tax_obj = self.env['qdodoo.car.pad.tax']
        # 判断是否存在押汇
        tax_id = tax_obj.search([('purchase_id','=',self.id),('state','!=','cancel')])
        if not tax_id:
            # 创建对应的垫税
            value = {}
            value['purchase_id'] = self.id
            tax_id = tax_obj.create(value)
        result = self.env['ir.model.data'].get_object_reference( 'qdodoo_car_import_trade', 'view_tree_qdodoo_car_pad_tax')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'view_form_qdodoo_car_pad_tax')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('垫税'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.pad.tax',
              'type': 'ir.actions.act_window',
              'domain':[('id','=',tax_id.id)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

    # 费用列表
    @api.multi
    def btn_expense_in_line(self):
        expense_obj = self.env['qdodoo.car.expense.in']
        # 查询对应的费用录入
        expense_id = expense_obj.search([('purchase_id','=',self.id)])
        result = self.env['ir.model.data'].get_object_reference( 'qdodoo_car_import_trade', 'tree_qdodoo_car_expense_in')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'form_qdodoo_car_expense_in')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('费用录入'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.expense.in',
              'type': 'ir.actions.act_window',
              'domain':[('id','in',expense_id.ids)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

    @api.multi
    # 费用
    def btn_expense_in(self):
        expense_obj = self.env['qdodoo.car.expense.in']
        expense_line_obj = self.env['qdodoo.car.expense.in.line']
        information_obj = self.env['qdodoo.car.information']
        # 创建对应的费用录入
        value = {}
        value['purchase_id'] = self.id
        value['date_order'] = datetime.now().date()
        expense_id = expense_obj.create(value)
        # 创建明细
        information_ids = information_obj.search([('purchase_id','=',self.id)])
        for information_id in information_ids:
            expense_line_obj.create({'expense_id':expense_id.id,'product_num':information_id.id})
        result = self.env['ir.model.data'].get_object_reference( 'qdodoo_car_import_trade', 'tree_qdodoo_car_expense_in')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'form_qdodoo_car_expense_in')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('费用录入'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.expense.in',
              'type': 'ir.actions.act_window',
              'domain':[('id','=',expense_id.id)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

    @api.multi
    # 结算
    def btn_settlement(self):
        settlement_obj = self.env['qdodoo.car.settlement']
        # 判断是否存在押汇
        settlement_id = settlement_obj.search([('purchase_id','=',self.id),('state','!=','cancel')])
        if not settlement_id:
            # 创建对应的垫税
            value = {}
            value['purchase_id'] = self.id
            settlement_id = settlement_obj.create(value)
        result = self.env['ir.model.data'].get_object_reference( 'qdodoo_car_import_trade', 'tree_qdodoo_car_settlement')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'form_qdodoo_car_settlement')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('结算'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.settlement',
              'type': 'ir.actions.act_window',
              'domain':[('id','=',settlement_id.id)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

    @api.multi
    # TT
    def btn_tt(self):
        issuing_obj = self.env['qdodoo.car.issuing.manager']
        # 判断是否存在TT申请
        issuing_id = issuing_obj.search([('type','=','tt'),('purchase_id','=',self.id),('state','!=','cancel')])
        if not issuing_id:
            # 创建对应的开证申请
            value = {}
            value['purchase_id'] = self.id
            value['issuing_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            value['payment_type'] = self.payment_type.name
            value['type'] = 'tt'
            value['buy_rate'] = 1/self.currency_id.rate_silent
            issuing_id = issuing_obj.create(value)
            # 创建对应的明细
            for line in self.order_line:
                line.copy({'issuing_id':issuing_id.id,'purchase_id':''})
        result = self.env['ir.model.data'].get_object_reference( 'qdodoo_car_import_trade', 'tree_qdodoo_car_issuing_manager')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'form_qdodoo_car_issuing_manager')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('TT付款'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.issuing.manager',
              'type': 'ir.actions.act_window',
              'domain':[('id','=',issuing_id.id)],
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

class qdodoo_car_purchase_contract_line(models.Model):
    _name = 'qdodoo.car.purchase.contract.line'

    purchase_id = fields.Many2one('qdodoo.car.purchase.contract',u'外贸合同')
    issuing_id = fields.Many2one('qdodoo.car.issuing.manager',u'信用证')
    sale_line = fields.Many2one('qdodoo.car.sale.contract.line',u'销售明细')
    product_id = fields.Many2one('product.product',u'车辆型号')
    product_qty = fields.Integer(u'数量')
    price_unit = fields.Float(u'单价')
    all_money = fields.Float(u'总价款',compute="_get_all_money")

    @api.onchange('product_id')
    def _onchange_line(self):
        if not self.purchase_id.contract_id:
            raise osv.except_osv(_('警告!'),_("请先选择一个销售合同！"))

    # 计算总价款
    def _get_all_money(self):
        for ids in self:
            ids.all_money = ids.price_unit * ids.product_qty

class qdodoo_car_payment_type(models.Model):
    """
        付款方式
    """
    _name = 'qdodoo.car.payment.type'

    name = fields.Char(u'付款方式')
    active = fields.Boolean(u'有效',default=True)

class qdodoo_car_purchase_bill_line(models.TransientModel):
    _name = 'qdodoo.car.purchase.bill.line'

    order_id = fields.Many2one('qdodoo.car.purchase.contract',u'外贸合同', default=lambda self:self._context.get('active_id'))
    line = fields.Many2many('qdodoo.car.information','qdodoo_purchase_car_info_rel', 'purchase_id','car_id', string=u'车辆明细')

    @api.multi
    # 创建/查看提单
    def btn_create_bill(self):
        order_id = self._context.get('active_id')
        purchase_obj = self.env['qdodoo.car.purchase.contract']
        bill_obj = self.env['qdodoo.car.bill.lading']
        bill_line_obj = self.env['qdodoo.car.bill.lading.line']
        is_create = self._context.get('create')
        if is_create:
            if not self.line:
                raise osv.except_osv(_(u'警告'),_(u'没有选择需要生成提单的车辆！'))
            purchas_id = purchase_obj.browse(order_id)
            res_id = bill_obj.create({'purchase_id':purchas_id.id,'in_port':purchas_id.out_port.id,'out_port':purchas_id.in_port.id})
            for line in self.line:
                bill_line_obj.create({'information_id':line.id,'bill_id':res_id.id,'product_id':line.product_id.id,'product_num':line.product_num,'price_unit':line.price_unit,'real_price':line.price_unit})
        else:
            # 查询已有的提单
            res_id = bill_obj.search([('purchase_id','=',order_id)])
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