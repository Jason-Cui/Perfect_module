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

class qdodoo_car_information(models.Model):
    """
        车辆档案
    """
    _name = 'qdodoo.car.information'
    _rec_name = 'product_num'
    _order = 'id desc'

    product_id = fields.Many2one('product.product',u'车辆型号')
    product_num = fields.Char(u'车架号')
    sale_contract = fields.Many2one('qdodoo.car.sale.contract',u'销售合同号')
    partner_id = fields.Many2one('res.partner',u'客户', related="sale_contract.partner_id")
    price_unit = fields.Float(u'销售合同价格')
    tax_money = fields.Float(u'销售合同税费')
    pledge_money = fields.Float(u'销售合同保证金')
    all_car_money = fields.Float(u'预收款')
    agent_money = fields.Float(u'代理费')
    purchase_id = fields.Many2one('qdodoo.car.purchase.contract',u'外贸合同号')
    negotiation_id = fields.Many2one('qdodoo.car.negotiation.manager',u'押汇协议号')
    currency_id = fields.Many2one('res.currency',u'开证币种')
    purchase_currency_id = fields.Many2one('res.currency',u'外贸合同币种')
    issuing_money = fields.Float(u'开证金额')
    negotiation_exchange_rate = fields.Float(u'押汇汇率(银行)')
    negotiation_date = fields.Date(u'押汇日期')
    negotiation_end_date = fields.Date(u'押汇截止日期')
    negotiation_rate = fields.Float(u'押汇利率(银行)')
    negotiation_interest = fields.Float(u'押汇利息(银行)')
    issuing_type = fields.Selection([('near',u'即期'),('long',u'90天远期')],u'信用证类型')
    bill_id = fields.Many2one('qdodoo.car.bill.lading',u'提单号')
    buy_exchange_rate = fields.Float(u'购汇汇率')
    sale_price = fields.Float(u'进口裸车价', compute='_get_sale_price')
    inspection_price = fields.Float(u'监装费')
    in_tax = fields.Float(u'进口关税')
    in_sale_tax = fields.Float(u'进口消费税')
    commodity_money = fields.Float(u'商检费')
    product_money = fields.Float(u'货代费')
    stock_money = fields.Float(u'仓储费')
    other_money = fields.Float(u'其他')
    three_issure = fields.Float(u'三包险')
    ship_issure = fields.Float(u'海运险')
    one_total = fields.Float(u'小计', compute="_get_one_total")
    issuing_cost = fields.Float(u'开证费用')
    customs_interest = fields.Float(u'海关垫支利息')
    delay_car_interest = fields.Float(u'延期赎车利息')
    no_tax_price = fields.Float(u'不含税开票价格')
    in_add_tax = fields.Float(u'海关进口增值税')
    forwarding_add_tax = fields.Float(u'货代增值税')
    sale_tax = fields.Float(u'销项税')
    add_tax = fields.Float(u'进口增值税')
    all_total = fields.Float(u'合计金额')
    negotiation_money = fields.Float(u'押汇金额',related="issuing_money")
    make_invoice = fields.Many2one('qdodoo.car.make.invoice',u'开票申请')
    contract_date = fields.Datetime(u'销售合同日期')
    purchase_date = fields.Datetime(u'外贸合同日期')
    issuing_date = fields.Datetime(u'开证日期')
    source_location = fields.Many2one('stock.location',u'源库位')
    dest_location = fields.Many2one('stock.location',u'现库位')
    out_ship = fields.Datetime(u'离港日期')
    in_ship = fields.Datetime(u'到港日期')
    open_box = fields.Datetime(u'拆箱日期')
    in_stock = fields.Datetime(u'入库日期')
    out_stock = fields.Datetime(u'出库日期')
    wait_take = fields.Datetime(u'库存调拨日期')
    done_date = fields.Datetime(u'交车日期')
    pad_tax_date = fields.Date(u'垫税日期')
    pad_tax_end_date = fields.Date(u'垫税截止日期')
    tax_price = fields.Float(u'开票价格')
    settle_price = fields.Float(u'结算价格')
    pad_agent = fields.Float(u'垫税代理费')
    purchase_price = fields.Float(u'外贸合同价格')
    issuing_id = fields.Many2one('qdodoo.car.issuing.manager',u'信用证编号')
    pad_id = fields.Many2one('qdodoo.car.pad.tax',u'垫税协议号')
    tax_id = fields.Char(u'税单号')
    pad_money = fields.Float(u'垫税金额',compute="_get_pad_money")
    pad_rate = fields.Float(u'垫税利率')
    pad_interest = fields.Float(u'垫税利息')
    margin_id = fields.Many2one('qdodoo.car.margin.money',u'二次保证金')
    carry_id = fields.Many2one('qdodoo.car.carry.money',u'提车款')
    margin_money = fields.Float(u'二次保证金金额')
    negotiation_sale_id = fields.Many2one('qdodoo.car.negotiation.manager.sale',u'客户押汇协议号')
    negotiation_sale_exchange_rate = fields.Float(u'押汇汇率(客户)')
    negotiation_sale_rate = fields.Float(u'押汇利率(客户)')
    negotiation_sale_interest = fields.Float(u'押汇利息(客户)')
    clearance_money = fields.Float(u'清关费用')
    all_issure = fields.Float(u'保险费')
    bank_money = fields.Float(u'银行手续费')
    logistics_money = fields.Float(u'物流费用')
    pad_tax_money = fields.Float(u'开票费用')
    delayed_moeny = fields.Float(u'滞报金')
    in_issuing_money = fields.Float(u'海关保证金')
    invoice_issuing_money = fields.Float(u'开证保证金')
    other_issuing_money = fields.Float(u'其他保证金')
    negotiation_over = fields.Boolean(u'结汇完成')
    dalay_date = fields.Float(u'延期天数', default='90')
    dalay_rate = fields.Float(u'延期利率(%)外币', default='4.5')

    # 获取进口裸车价
    def _get_sale_price(self):
        for ids in self:
            if ids.sale_contract:
                ids.sale_price = ids.price_unit * ids.sale_contract.currency_raise

    # 获取垫税金额
    def _get_pad_money(self):
        for ids in self:
            ids.pad_money = ids.in_tax + ids.in_sale_tax + ids.add_tax

    # 获取小计
    def _get_one_total(self):
        for ids in self:
            ids.one_total = ids.purchase_price+ids.inspection_price+ids.in_tax+ids.in_sale_tax+ids.commodity_money+ids.product_money+ids.stock_money+ids.other_money+ids.three_issure+ids.ship_issure

    _sql_constraints = [
        ('product_num_uniq', 'unique(product_num)',
            '车架号已存在!'),
    ]

    # 判断车架号位数
    @api.model
    def create(self, vals):
        if vals.get('product_num') and len(vals.get('product_num')) != 17:
            raise osv.except_osv(_(u'警告'),_(u'车架号必须为17位！'))
        return super(qdodoo_car_information, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('product_num') and len(vals.get('product_num')) != 17:
            raise osv.except_osv(_(u'警告'),_(u'车架号必须为17位！'))
        return super(qdodoo_car_information, self).write(vals)
