from flask_login import current_user


# --- 权限管理部分 ---

def get_user_permissions(user_role):
    """根据用户角色返回权限字典。"""
    permissions = {
        0: {'can_manage_users': False, 'can_manage_supplies': False, 'can_edit_permissions': False},  # 普通员工
        1: {'can_manage_users': False, 'can_manage_supplies': True, 'can_edit_permissions': False},  # 设计部门负责人
        2: {'can_manage_users': False, 'can_manage_supplies': True, 'can_edit_permissions': False},  # 生产部门负责人
        3: {'can_manage_users': False, 'can_manage_supplies': True, 'can_edit_permissions': False},  # 仓库管理员
        4: {'can_manage_users': False, 'can_manage_supplies': True, 'can_edit_permissions': False},  # 车间领料人
        # ... 其他角色
    }

    if current_user.is_admin:  # 如果是管理员
        return {'can_edit_permissions': True}  # 只有修改权限的权限为 True

    return permissions.get(user_role[0] if user_role else None, {}) if user_role else {}  # 修复: 处理角色为空或不存在的情况


def get_user_data():
    """获取当前用户的权限和其他数据"""
    user = current_user
    try:  # 处理角色可能为空的情况
        user_roles = [int(r.strip()) for r in user.role.split(',') if r.strip()] if user.role else []
    except ValueError:
        user_roles = []

    user_permissions = get_user_permissions(user_roles)

    data = {
        'current_user': user,
    }
    data.update(user_permissions)  # 将权限添加到 data 字典

    return data