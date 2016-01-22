# -*- coding: utf-8 -*-
###########################################################################################
#
# module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

{
    'name': '需求转换单',  # 模块名称
    'version': '1.0',  # 版本
    'category': 'Technology',  # 分类
    'author': 'qdodoo Technology',  # 作者
    'website': 'http://www.qdodoo.com/',  # 网址
    'summary': '',  # 摘要
    'images': [],  # 模块图片
    'depends': ['base', 'stock', 'procurement'],  # 依赖模块
    'data': [
        'qdodoo_stock_demand_view.xml',
        'qdodoo_stock_demand_sequence_view.xml',
        'qdodoo_procurement_order_inhert.xml',
        'wizard/qdodoo_return_demand_wiazrd.xml'
        # 'qdodoo_stock_demand_inherit_view.xml'
        # 'security/account_security.xml',
        # ...
    ],  # 更新XML,CSV
    'js': [
        # 'static/src/js/account_move_reconciliation.js',
        # ...
    ],  # javascript
    'qweb': [
        # "static/src/xml/account_move_reconciliation.xml",
        # ...
    ],
    'css': [
        # 'static/src/css/account_move_reconciliation.css',
        # ...
    ],  # css样式
    'demo': [
        # 'demo/account_demo.xml',
        # ...
    ],
    'test': [
        # 'test/account_customer_invoice.yml',
        # ...
    ],  # 测试
    'application': True,  # 是否认证
    'installable': True,  # 是否可安装
    'auto_install': False,  # 是否自动安装
    'description': """
    功能：1.新建需求转换单模型，批量处理需求单
         2.移库单增加需求反向，如果源单据是需求转换单则可以反向逆推成需求转换单
    """,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
