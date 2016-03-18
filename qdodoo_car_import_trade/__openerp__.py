# -*- coding: utf-8 -*-
###########################################################################################
#
#    module name for Qdodoo suifeng
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

{
    'name': '汽车外贸管理模块',  # 模块名称
    'version': '1.0',  # 版本
    'category': 'Technology',  # 分类
    'author': 'qdodoo',  # 作者
    'website': 'http://www.qdodoo.com/',  # 网址
    'summary': '',  # 摘要
    'images': [],  # 模块图片
    'depends': ['base', 'sale','purchase'],  # 依赖模块
    'data': [
        'views/all_menuitem.xml',
        'views/qdodoo_car_sale_contract.xml',
        'qdodoo_car_import_trade_sequence.xml',
        'qdodoo_car_import_trade_data.xml',
        'views/qdodoo_car_information.xml',
        'views/qdodoo_car_pledge_money.xml',
        'views/qdodoo_car_payment_order.xml',
        'views/qdodoo_car_purchase_contract.xml',
        'views/qdodoo_car_port_manager.xml',
        'views/qdodoo_car_issuing_manager.xml',
        'views/qdodoo_car_negotiation_manager.xml',
        'views/qdodoo_car_bill_lading.xml',
        'views/qdodoo_car_expense_in.xml',
        'views/qdodoo_car_stock.xml',
        'views/qdodoo_car_pad_tax.xml',
        'views/qdodoo_car_make_invoice.xml',
        'views/qdodoo_car_selecte.xml',
        'views/qdodoo_car_margin_money.xml',
        'views/qdodoo_car_carry_money.xml',
        'views/qdodoo_car_settlement.xml',
        'views/report_sale_contract.xml',
        'views/report_purchase_contract.xml',
        'views/report_car_make_invoice.xml',
        'views/report_purchase_contract_workflow.xml',
        'views/report_payment_order.xml',
        'qdodoo_car_report.xml',
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

    """,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
