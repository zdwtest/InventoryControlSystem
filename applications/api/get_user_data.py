from flask import get_flashed_messages
from flask_login import current_user

from applications.database.database import Users


def get_user_data():
    # 获取当前用户
    user = current_user

    # 获取用户权限
    user_permissions = Users.select().where(Users.id == user.id).get()
    can_manage_users = user_permissions.can_manage_users
    can_manage_supplies = user_permissions.can_manage_supplies
    can_manage_suppliers = user_permissions.can_manage_suppliers
    can_manage_products = user_permissions.can_manage_products
    can_manage_purchases = user_permissions.can_manage_purchases
    can_manage_quality_controls = user_permissions.can_manage_quality_controls
    can_manage_warehouses = user_permissions.can_manage_warehouses
    can_manage_finances = user_permissions.can_manage_finances

    # 创建数据字典
    data = {
        'current_user': user,
        'can_manage_users': can_manage_users,
        'can_manage_supplies': can_manage_supplies,
        'can_manage_suppliers': can_manage_suppliers,
        'can_manage_products': can_manage_products,
        'can_manage_purchases': can_manage_purchases,
        'can_manage_quality_controls': can_manage_quality_controls,
        'can_manage_warehouses': can_manage_warehouses,
        'can_manage_finances': can_manage_finances,
        'messages': get_flashed_messages()
    }
    return data
