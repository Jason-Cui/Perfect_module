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

class qdodoo_car_negotiation_manager(models.Model):
    """
        押汇管理
    """
    _name = 'qdodoo.car.negotiation.manager'
    _order = 'id desc'

    name = fields.Char(u'押汇申请编号')
    purchase_id = fields.Many2one('qdodoo.car.purchase.contract',u'外贸合同号')
    bill_id = fields.Many2one('qdodoo.car.bill.lading',u'提单号')
    issuing_type = fields.Selection([('near',u'即期'),('long',u'90天远期')],u'信用证类型', related="purchase_id.issuing_id.issuing_type")
    negotiation_date = fields.Date(u'押汇日期')
    state = fields.Selection([('draft',u'草稿'),('doing',u'押汇'),('done',u'完成'),('cancel',u'取消')],u'状态',default='draft')
    order_line = fields.One2many('qdodoo.car.negotiation.manager.line','negotiation_id',u'车辆明细')
    negotiation_rate = fields.Float(u'押汇利率', related="purchase_id.contract_id.dalay_rate")
    dalay_china_rate = fields.Float(u'延期利率', related="purchase_id.contract_id.dalay_china_rate")

    # 获取唯一的编号
    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].get('qdodoo.car.negotiation.manager')
        return super(qdodoo_car_negotiation_manager, self).create(vals)

    # 根据提单号获取车辆明细
    @api.onchange('bill_id')
    def _get_order_lie(self):
        car_obj = self.env['qdodoo.car.information']
        self.order_line = ''
        lst = []
        for line in car_obj.search([('bill_id','=',self.bill_id.id)]):
            lst.append((0,0,{'product_num':line.id,'product_id':line.product_id.id,'currency_id':line.currency_id.id,'negotiation_money':line.negotiation_money,
                             'negotiation_exchange_rate':line.negotiation_exchange_rate,'negotiation_end_date':line.negotiation_end_date,
                             'negotiation_interest':line.negotiation_interest}))
        self.order_line = lst

    # 确认(更新车辆档案里的押汇信息,根据条件判断是否更新开证申请状态)
    @api.one
    def btn_doing(self):
        for line in self.order_line:
            line.product_num.write({'negotiation_id':self.id,'negotiation_exchange_rate':line.negotiation_exchange_rate,'negotiation_date':self.negotiation_date,
                                    'negotiation_end_date':line.negotiation_end_date})
        # 如果外贸合同下所有的车辆档案都更新了押汇单号，更新开证申请的状态
        car_ids = self.env['qdodoo.car.information'].search([('purchase_id','=',self.purchase_id.id),('negotiation_id','=',False)])
        if not car_ids:
            self.purchase_id.issuing_id.write({'state':'done'})
        return self.write({'state':'doing'})

    # 取消
    @api.one
    def btn_cancel(self):
        return self.write({'state':'cancel'})

    # 结汇(生成付款申请，更细车辆档案信息)
    @api.multi
    def btn_done(self):
        # 统计可以结汇的车辆档案
        car_lst = []
        for line in self.order_line:
            # 如果未结汇并且有到期日期，更新车辆档案信息
            if not line.product_num.negotiation_over and line.negotiation_end_date:
                car_lst.append(line)
                line.product_num.write({'negotiation_over':True,'negotiation_exchange_rate':line.negotiation_exchange_rate,'negotiation_end_date':line.negotiation_end_date,'negotiation_date':self.negotiation_date,'negotiation_interest':line.negotiation_interest})
        if car_lst:
            model_id, pay_project= self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade','qdodoo_car_expense_4')
            payment_id = self.env['qdodoo.car.payment.order'].create({'type':'payment','partner_id':self.purchase_id.issuing_id.partner_id.id,'purchase_id':self.purchase_id.id,'pay_project_2':pay_project})
            for line_obj in car_lst:
                self.env['qdodoo.car.payment.line'].create({'order_id':payment_id.id,'product_num':line_obj.product_num.id,'money':line_obj.negotiation_money*line_obj.negotiation_exchange_rate+line_obj.negotiation_interest-line_obj.product_num.invoice_issuing_money})
        else:
            raise osv.except_osv(_(u'警告'),_(u'没有需要结汇的车辆！'))
        # 判断是否全部结汇完成
        log = True
        for line in self.order_line:
            if not line.product_num.negotiation_over or not line.negotiation_end_date:
                log = False
        if log:
            self.write({'state':'done'})
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

class qdodoo_car_negotiation_manager_line(models.Model):
    _name = 'qdodoo.car.negotiation.manager.line'

    negotiation_id = fields.Many2one('qdodoo.car.negotiation.manager',u'押汇单')
    product_id = fields.Many2one('product.product',u'车辆型号')
    product_num = fields.Many2one('qdodoo.car.information',u'车架号')
    currency_id = fields.Many2one('res.currency',u'币种')
    negotiation_money = fields.Float(u'押汇金额')
    negotiation_exchange_rate = fields.Float(u'押汇汇率')
    negotiation_end_date = fields.Date(u'到期日期')
    negotiation_interest = fields.Float(u'押汇利息(银行)',compute="_get_negotiation_interest")

    # 获取押汇利息
    def _get_negotiation_interest(self):
        for ids in self:
            if ids.negotiation_end_date and ids.negotiation_id.negotiation_date:
                if ids.negotiation_id.issuing_type == 'near':
                    dalay_date = ids.product_num.dalay_date
                    date_poor = (datetime.strptime(ids.negotiation_end_date,'%Y-%m-%d') - datetime.strptime(ids.negotiation_id.negotiation_date,'%Y-%m-%d')).days
                    if date_poor <= dalay_date:
                        ids.negotiation_interest = ids.negotiation_money * ids.negotiation_exchange_rate * ids.negotiation_id.negotiation_rate * date_poor/365 * (1 - ids.product_num.purchase_id.issuing_id.issuing_payment_rate/100)
                    else:
                        ids.negotiation_interest = ids.negotiation_money * ids.negotiation_exchange_rate * ids.negotiation_id.negotiation_rate * dalay_date/365 * (1 - ids.product_num.purchase_id.issuing_id.issuing_payment_rate/100) + ids.negotiation_money * ids.negotiation_exchange_rate * ids.dalay_china_rate * (date_poor-dalay_date)/365
                else:
                    ids.negotiation_interest =  ids.negotiation_money * ids.negotiation_exchange_rate * ids.dalay_china_rate * (date_poor-dalay_date)/365 * (1 - ids.product_num.purchase_id.issuing_id.issuing_payment_rate/100)
            if ids.negotiation_interest <= 0:
                ids.negotiation_interest = 0

class qdodoo_car_negotiation_manager_sale(models.Model):
    """
        押汇-销售
    """
    _name = 'qdodoo.car.negotiation.manager.sale'
    _order = 'id desc'

    name = fields.Char(u'编号')
    negotiation_name = fields.Char(u'押汇协议号')
    purchase_id = fields.Many2one('qdodoo.car.purchase.contract',u'外贸合同号')
    state = fields.Selection([('draft',u'草稿'),('doing',u'押汇'),('done',u'完成'),('cancel',u'取消')],u'状态',default='draft')
    bill_id = fields.Many2one('qdodoo.car.bill.lading',u'提单号')
    issuing_type = fields.Selection([('near',u'即期'),('long',u'90天远期')],u'信用证类型', related="purchase_id.issuing_id.issuing_type")
    file_name = fields.Char(u'文件名称', copy=False)
    negotiation_file = fields.Binary(u'协议原件', copy=False)
    order_line = fields.One2many('qdodoo.car.negotiation.manager.sale.line','negotiation_sale_id',u'车辆明细')
    negotiation_rate = fields.Float(u'押汇利率', related="purchase_id.contract_id.dalay_rate")
    dalay_china_rate = fields.Float(u'延期利率', related="purchase_id.contract_id.dalay_china_rate")

    # 获取唯一的编号
    @api.model
    def create(self, vals):
        if not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].get('qdodoo.car.negotiation.manager')
        return super(qdodoo_car_negotiation_manager_sale, self).create(vals)

    # 根据提单号获取车辆明细
    @api.onchange('bill_id')
    def _get_order_lie(self):
        car_obj = self.env['qdodoo.car.information']
        self.order_line = ''
        lst = []
        for line in car_obj.search([('bill_id','=',self.bill_id.id)]):
            lst.append((0,0,{'negotiation_end_date':line.negotiation_end_date,'negotiation_date':line.negotiation_date,'product_num':line.id,'product_id':line.product_id.id,'currency_id':line.currency_id.id,'negotiation_money':line.negotiation_money,
                             'negotiation_sale_exchange_rate':line.negotiation_sale_exchange_rate,'negotiation_end_date':line.negotiation_end_date,
                             'negotiation_sale_interest':line.negotiation_sale_interest}))
        self.order_line = lst

    # 确认(更新车辆档案里的押汇信息)
    @api.one
    def btn_doing(self):
        for line in self.order_line:
            line.product_num.write({'negotiation_sale_id':self.id,'negotiation_sale_exchange_rate':line.negotiation_sale_exchange_rate})
        return self.write({'state':'doing'})

    # 取消
    @api.one
    def btn_cancel(self):
        return self.write({'state':'cancel'})

    # 结汇(判断所有的汇率和到期日期都已经填写,更新车辆档案信息)
    @api.one
    def btn_done(self):
        for line in self.order_line:
            if not line.negotiation_sale_exchange_rate:
                raise osv.except_osv(_(u'警告'),_(u'请输入所有车辆的押汇汇率！'))
            line.product_num.write({'negotiation_sale_exchange_rate':line.negotiation_sale_exchange_rate,'negotiation_sale_interest':line.negotiation_sale_interest})
        return self.write({'state':'done'})

class qdodoo_car_negotiation_manager_sale_line(models.Model):
    _name = 'qdodoo.car.negotiation.manager.sale.line'

    negotiation_sale_id = fields.Many2one('qdodoo.car.negotiation.manager.sale',u'押汇单')
    product_id = fields.Many2one('product.product',u'车辆型号')
    currency_id = fields.Many2one('res.currency',u'币种')
    negotiation_money = fields.Float(u'押汇金额')
    negotiation_sale_exchange_rate = fields.Float(u'押汇汇率')
    negotiation_end_date = fields.Date(u'到期日期')
    negotiation_date = fields.Date(u'押汇日期')
    negotiation_sale_interest = fields.Float(u'押汇利息', compute="_get_negotiation_sale_interest")
    product_num = fields.Many2one('qdodoo.car.information',u'车架号')

    # dalay_date
    # 获取押汇利息
    def _get_negotiation_sale_interest(self):
        for ids in self:
            # 获取延期日期
            dalay_date = ids.product_num.dalay_date
            date_poor = (datetime.strptime(ids.negotiation_end_date,'%Y-%m-%d') - datetime.strptime(ids.negotiation_date,'%Y-%m-%d')).days
            if ids.negotiation_sale_id.issuing_type == 'near':
                if date_poor <= dalay_date:
                    negotiation_sale_interest = ids.negotiation_money * ids.negotiation_sale_exchange_rate * ids.negotiation_sale_id.negotiation_rate * date_poor/365 * (1 - ids.product_num.sale_contract.deposit_rate/100)
                else:
                    negotiation_sale_interest = ids.negotiation_money * ids.negotiation_sale_exchange_rate * ids.negotiation_sale_id.negotiation_rate * dalay_date/365 * (1 - ids.product_num.sale_contract.deposit_rate/100) + ids.negotiation_money * ids.negotiation_sale_exchange_rate * ids.dalay_china_rate * (date_poor-dalay_date)/365
            else:
                if date_poor <= dalay_date:
                    negotiation_sale_interest = 0
                else:
                    negotiation_sale_interest = ids.negotiation_money * ids.negotiation_sale_exchange_rate * ids.dalay_china_rate * (date_poor-dalay_date)/365 * (1 - ids.product_num.sale_contract.deposit_rate/100)
            if negotiation_sale_interest <= 0:
                ids.negotiation_sale_interest = 0
            else:
                ids.negotiation_sale_interest = negotiation_sale_interest