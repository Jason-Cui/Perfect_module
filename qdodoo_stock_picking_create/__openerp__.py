# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

{
    'name': u'物流核算收货自动创建发票',  # 模块名称
    'version': '1.0',  # 版本
    'category': 'Technology',  # 分类
    'author': 'qdodoo Technology',  # 作者
    'website': 'http://www.qdodoo.com/',  # 网址
    'summary': '',  # 摘要
    'images': [],  # 模块图片
    'depends': ['base', 'stock', 'stock_account'],  # 依赖模块
    'data': [

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
    基于业务生成的移库单，入库完成后，自动生成发票，发票日期默认为入库日期
    """,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
