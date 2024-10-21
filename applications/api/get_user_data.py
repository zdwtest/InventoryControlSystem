from flask import get_flashed_messages
from flask_login import current_user

from applications.database.database import Users


def get_user_data():
    user = current_user
    role = user.role

    permissions = {
        'admin': {
            'can_manage_users': True,
            'can_manage_supplies': True,
            # ... 所有权限都是 True
        },
        'manager': {
            'can_manage_users': False,
            'can_manage_supplies': True,
            # ... 部分权限是 True
        },
        'staff': {
            'can_manage_users': False,
            'can_manage_supplies': False,
            # ... 大部分权限是 False
        },
        # ...其他角色
    }

    user_permissions = permissions.get(role, {}) # 获取当前用户的权限，如果角色不存在，则使用空字典

    data = {
        'current_user': user,
        'can_manage_users': user_permissions.get('can_manage_users', False),
        'can_manage_supplies': user_permissions.get('can_manage_supplies', False),
        # ... 其他权限，使用类似的 .get() 方法，并提供默认值 False
        'messages': get_flashed_messages()
    }
    return data