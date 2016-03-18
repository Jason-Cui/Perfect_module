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
class qdodoo_car_make_invoice(models.Model):
    """
        开票申请
    """
    _name = 'qdodoo.car.make.invoice'    # 模型名称
    _order = 'id desc'

    name = fields.Char(u'申请单号')
    contract_id = fields.Many2one('qdodoo.car.sale.contract',u'销售合同号')
    invoice_type = fields.Selection([('add_tax',u'增值税发票')],u'发票类型')
    partner_id = fields.Many2one('res.partner',u'客户')
    address = fields.Char(u'地址',related="partner_id.street")
    phone = fields.Char(u'电话',related="partner_id.phone")
    date = fields.Date(u'发票日期')
    invoice_name = fields.Char(u'发票号')
    tax_person_num = fields.Char(u'纳税人识别号',related="partner_id.tax_person_num")
    bank_id = fields.Many2one('res.bank',u'开户银行')
    account_id = fields.Char(u'账号')
    bank_address = fields.Char(u'银行地址')
    order_line = fields.One2many('qdodoo.car.information','make_invoice',u'车辆明细')
    notes = fields.Text(u'备注')
    state = fields.Selection([('draft', u'草稿'),('doing', u'登记'),('done', u'完成')
                              ,('cancel', u'取消')], u'状态',default='draft')
    all_money = fields.Float(u'开票金额',compute="_get_all_money")
    car_number = fields.Float(u'车辆数',compute="_get_all_money")

    def _get_all_money(self):
        for ids in self:
            ids.all_money = 0
            ids.car_number = 0
            for line in ids.order_line:
                ids.all_money += line.all_total
                ids.car_number += 1

    # 获取唯一的编号
    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].get('qdodoo.car.make.invoice')
        return super(qdodoo_car_make_invoice, self).create(vals)

    # 确认
    @api.one
    def btn_doing(self):
        return self.write({'state':'doing'})

    # 取消
    @api.one
    def btn_cancel(self):
        return self.write({'state':'cancel'})

    # 登记完成
    @api.one
    def btn_done(self):
        return self.write({'state':'done'})

    # 金额明细
    @api.multi
    def btn_car_information(self):
        result = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'tree_qdodoo_car_information_2')
        view_id = result and result[1] or False
        return {
              'name': _('开票金额明细'),
              'view_type': 'form',
              "view_mode": 'tree',
              'res_model': 'qdodoo.car.information',
              'type': 'ir.actions.act_window',
              'domain':[('id','in',self.order_line.ids)],
              'view_id': [view_id],
        }

class qdodoo_res_partner_inherit(models.Model):
    _inherit = 'res.partner'

    tax_person_num = fields.Char(u'纳税人识别号')