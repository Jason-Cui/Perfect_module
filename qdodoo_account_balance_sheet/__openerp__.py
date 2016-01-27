# -*- coding: utf-8 -*-
###########################################################################################
#    author:Adger Zhou
#    module name for OpenERP
#    Copyright (C) 2015 qdodoo Technology CO.,LTD. (<http://www.qdodoo.com/>).
#
###########################################################################################

{
    'name': "中国会计--科目余额表",
    'version': '1.1',
    'author': 'Adger Zhou',
    'category': 'Account',
    'sequence': 21,
    'website': 'https://www.qdodoo.com',
    # 'summary': 'Jobs, Departments, Employees Details',
    'description': """
    科目余额表:根据会计期间搜索，组合数据数据
    报表分三层:
    第一层:按公司组合每个科目的期初余额，借方金额，贷方金额,期末余额
    第二层:点击第一层Tree视图即可查看第二层,根据该科目下，每个合作伙伴拆分
    第三层:点击第二层即可查看合作伙伴对应明细
    菜单:会计》表》科目余额表
    """,
    'images': [
    ],
    'depends': ['account'],
    'data': [
        'wizard/qdodoo_account_balance_wizard.xml',
        'report/qdodoo_account_balance_report.xml'
    ],
    'test': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
