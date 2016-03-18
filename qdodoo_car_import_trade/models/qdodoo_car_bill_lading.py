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

class qdodoo_car_bill_lading(models.Model):
    """
        提单
    """
    _name = 'qdodoo.car.bill.lading'    # 模型名称
    _order = 'id desc'

    name = fields.Char(u'提单编号')
    bill_name = fields.Char(u'提单号')
    bill_note = fields.Binary(u'提单原件')
    file_name = fields.Char(u'收获通知单名称')
    purchase_id = fields.Many2one('qdodoo.car.purchase.contract',u'外贸合同号')
    in_port = fields.Many2one('qdodoo.car.port.manager',u'发货港',domain=[('type','=','out')],related="purchase_id.out_port")
    out_port = fields.Many2one('qdodoo.car.port.manager',u'目的港',domain=[('type','=','in')],related="purchase_id.in_port")
    sale_id = fields.Many2one('qdodoo.car.sale.contract',u'销售合同号', related="purchase_id.contract_id")
    partner_id = fields.Many2one('res.partner',u'供应商', related="purchase_id.partner_id")
    partner_customer_id = fields.Many2one('res.partner',u'客户', related="purchase_id.contract_id.partner_id")
    left_ship_date = fields.Date(u'发运日期')
    into_ship_date = fields.Date(u'预计到达日期')
    order_line = fields.One2many('qdodoo.car.bill.lading.line','bill_id',u'货物明细')
    state = fields.Selection([('draft',u'草稿'),('done',u'完成'),('cancel',u'取消')],u'状态',default='draft')
    import_file = fields.Binary(string="导入的模板")
    broker_id = fields.Many2one('res.partner',u'报关行')
    shop_name = fields.Char(u'船名')
    shop_size = fields.Char(u'船次')

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].get('qdodoo.car.bill.lading')
        return super(qdodoo_car_bill_lading, self).create(vals)

    # 只能删除草稿或取消的订单
    @api.multi
    def unlink(self):
        for ids in self:
            if ids.state not in ('draft','cancel'):
                raise osv.except_osv(_(u'错误'),_(u'只能删除草稿或取消的订单！'))
        return super(qdodoo_car_bill_lading, self).unlink()

    # 确认（更新车辆档案中的车架号、提单号）
    @api.one
    def btn_confirmed(self):
        if not self.order_line:
            raise osv.except_osv(_(u'警告'),_(u'货物明细不能为空！'))
        for line in self.order_line:
            if not line.product_num:
                raise osv.except_osv(_(u'警告'),_(u'请输入车架号！'))
            line.information_id.write({'product_num':line.product_num,'bill_id':self.id})
        return self.write({'state':'done'})

    # 取消
    @api.one
    def btn_cancel(self):
        return self.write({'state':'cancel'})

    # 返回
    @api.one
    def btn_draft(self):
        return self.write({'state':'draft'})

    # 结汇
    @api.multi
    def btn_negotiation(self):
        payment_obj = self.env['qdodoo.car.payment.order']
        line_obj = self.env['qdodoo.car.payment.line']
        domain = [('type','=','payment'),('bill_id','=',self.id),('state','!=','cancel')]
        value = {'type':'payment','bill_id':self.id,'partner_id':self.partner_id.id}
        model_id, pay_project= self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade','qdodoo_car_expense_4')
        value['pay_project_2'] = pay_project
        # 判断是否存在付款通知
        payment_id = payment_obj.search(domain)
        if not payment_id:
            # 创建对应的付款申请
            payment_id = payment_obj.create(value)
            # 创建对应的付款明细
            for line in self.order_line:
                line_obj.create({'order_id':payment_id.id,'product_num':line.id})
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

class qdodoo_car_bill_lading_line(models.Model):
    """
        提单明细
    """
    _name = 'qdodoo.car.bill.lading.line'

    bill_id = fields.Many2one('qdodoo.car.bill.lading',u'提单')
    information_id = fields.Many2one('qdodoo.car.information',u'车辆档案id')
    product_id = fields.Many2one('product.product',u'车辆型号')
    product_num = fields.Char(u'车架号')
    price_unit = fields.Float(u'销售合同价格')
    box_num = fields.Char(u'箱号')