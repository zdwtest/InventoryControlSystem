# applications/api/get_user_data.py
from flask_login import current_user

def get_user_data():
    """获取当前登录用户的相关数据。"""
    if current_user.is_authenticated:
        return {
            'id': current_user.id,
            'username': current_user.username,
            'permissions': current_user.permissions, # 用户权限
            'is_admin': current_user.is_admin, # 是否是管理员
            'role': current_user.role, # 用户角色
            # ... 其他用户信息 ...
        }
    else:
        return {} # 未登录用户返回空字典