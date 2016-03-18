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

class qdodoo_car_settlement(models.Model):
    """
        结算单
    """
    _name = 'qdodoo.car.settlement'
    _order = 'id desc'

    name = fields.Char(u'编号')
    purchase_id = fields.Many2one('qdodoo.car.purchase.contract',u'外贸合同号')
    partner_id = fields.Many2one('res.partner',u'客户名称',related="purchase_id.contract_id.partner_id")
    sale_id = fields.Many2one('qdodoo.car.sale.contract',u'销售合同号',related="purchase_id.contract_id")
    state = fields.Selection([('draft',u'草稿'),('done',u'完成')],u'状态',default='draft')

    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].get('qdodoo.car.settlement')
        return super(qdodoo_car_settlement, self).create(vals)

    # 结算完成
    @api.one
    def btn_done(self):
        self.write({'state':'done'})

    # 结算明细
    @api.multi
    def btn_oder_line(self):
        pass
        # payment_obj = self.env['qdodoo.car.payment.order']
        # line_obj = self.env['qdodoo.car.payment.line']
        # domain = [('type','=','payment'),('bill_id','=',self.id),('state','!=','cancel')]
        # value = {'type':'payment','bill_id':self.id,'partner_id':self.partner_id.id}
        # model_id, pay_project= self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade','qdodoo_car_expense_4')
        # value['pay_project_2'] = pay_project
        # # 判断是否存在付款通知
        # payment_id = payment_obj.search(domain)
        # if not payment_id:
        #     # 创建对应的付款申请
        #     payment_id = payment_obj.create(value)
        #     # 创建对应的付款明细
        #     for line in self.order_line:
        #         line_obj.create({'order_id':payment_id.id,'product_num':line.id})
        # result = self.env['ir.model.data'].get_object_reference( 'qdodoo_car_import_trade', 'tree_qdodoo_car_settlement_line')
        # view_id = result and result[1] or False
        # result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'form_qdodoo_car_payment_order')
        # view_id_form = result_form and result_form[1] or False
        # return {
        #       'name': _('结算单明细'),
        #       'view_type': 'form',
        #       "view_mode": 'tree',
        #       'res_model': 'qdodoo.car.settlement.line',
        #       'type': 'ir.actions.act_window',
        #       'domain':[('id','=',payment_id.id)],
        #       'views': [(view_id,'tree')],
        #       'view_id': [view_id],
        # }

class qdodoo_car_settlement_line(models.Model):
    """
        结算单明细
    """
    _name = 'qdodoo.car.settlement.line'

    product_id = fields.Many2one('product.product',u'车辆型号')
    product_num = fields.Many2one('qdodoo.car.information',u'车架号')
    payment_money = fields.Float(u'已付金额')
    no_payment_money = fields.Float(u'应付金额')
    balance_money = fields.Float(u'差额')


