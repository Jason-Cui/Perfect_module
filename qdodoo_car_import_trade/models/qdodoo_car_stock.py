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
class qdodoo_car_stock(models.Model):
    """
        出入库管理
    """
    _name = 'qdodoo.car.stock'    # 模型名称
    _rec_name = 'port_id'
    _order = 'id desc'

    in_port_date = fields.Date(u'到港日期')
    box_date = fields.Date(u'拆箱日期')
    in_stock_date = fields.Date(u'入库日期')
    out_stock_date = fields.Date(u'出库日期')
    move_date = fields.Date(u'调拨日期')
    source_id = fields.Many2one('stock.location',u'源仓库')
    port_id = fields.Many2one('stock.location',u'库位',default=lambda self:self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade',self._context.get('view_id'))[1] if self._context.get('view_id') else '')
    state = fields.Selection([('draft',u'未移库'),('done',u'已移库')],u'状态',default="draft")
    order_line = fields.One2many('qdodoo.car.stock.line','order_id',u'车辆明细')

    # 转移
    @api.one
    def btn_done(self):
        write_dict = {}
        if self.in_port_date:
            write_dict['in_ship'] = self.in_port_date
        if self.box_date:
            write_dict['open_box'] = self.box_date
        if self.in_stock_date:
            write_dict['in_stock'] = self.in_stock_date
        if self.out_stock_date:
            write_dict['out_stock'] = self.out_stock_date
        if self.move_date:
            write_dict['wait_take'] = self.move_date
        if self.port_id:
            write_dict['dest_location'] = self.port_id.id
        if self.source_id:
            write_dict['source_location'] = self.source_id.id
        for line in self.order_line:
            line.product_num.write(write_dict)
        return self.write({'state':'done'})

    # 创建费用录入
    @api.multi
    def btn_expense_in(self):
        expense_obj = self.env['qdodoo.car.expense.in.car']
        # 获取所有的车辆档案id
        lst = []
        for line in self.order_line:
            lst.append(line.product_num.id)
        expense_ids = expense_obj.search([('expense_id','in',lst)])
        if not expense_ids:
            # 创建费用录入
            for line in self.order_line:
                expense_obj.create({'expense_id':line.product_num.id})
        result = self.env['ir.model.data'].get_object_reference( 'qdodoo_car_import_trade', 'tree_qdodoo_car_expense_in_car')
        view_id = result and result[1] or False
        result_form = self.env['ir.model.data'].get_object_reference('qdodoo_car_import_trade', 'form_qdodoo_car_expense_in_car')
        view_id_form = result_form and result_form[1] or False
        return {
              'name': _('费用录入'),
              'view_type': 'form',
              "view_mode": 'tree,form',
              'res_model': 'qdodoo.car.expense.in',
              'type': 'ir.actions.act_window',
              'domain':[('id','in',expense_ids.ids)],
              'context':{'type':('translation')},
              'views': [(view_id,'tree'),(view_id_form,'form')],
              'view_id': [view_id],
        }

class qdodoo_car_stock_line(models.Model):
    """
        出入库管理明细
    """
    _name = 'qdodoo.car.stock.line'    # 模型名称

    order_id = fields.Many2one('qdodoo.car.stock',u'出入库管理')
    product_num = fields.Many2one('qdodoo.car.information',u'车架号')
    product_id = fields.Many2one('product.product',u'车辆型号',related="product_num.product_id")
