from flask import curreent_user, LoginManager, flash, redirect, url_for
from flask_login import current_user

from applications.database.database import database, Users


# 管理员装饰器
def admin_required(func):
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated and current_user.is_admin:  # 只检查 is_admin
            return func(*args, **kwargs)
        else:
            flash('您没有权限访问此页面。', 'danger')
            return redirect(url_for('index'))

    wrapper.__name__ = func.__name__
    return wrapper

# 权限获取
def permission_get(user):
    if user.is_admin:
        print('admin')
        return 'admin'

    if user.role==1:
        print('role1')
        return 'role1'