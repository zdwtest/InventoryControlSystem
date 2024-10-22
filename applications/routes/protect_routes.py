from functools import wraps

from flask import flash, url_for, redirect, Blueprint
from flask_login import login_required, current_user

auth = Blueprint('protected', __name__)  # 创建蓝图，命名为 'protected'


# 管理员权限装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录。', 'error')
            return redirect(url_for('auth.login'))  # 使用蓝图名称
        elif not current_user.is_admin:  # 检查用户是否为管理员
            flash('您没有权限访问此页面。', 'error')
            return redirect(url_for('index'))  # 假设 'index' 路由不在蓝图中
        return f(*args, **kwargs)
    return decorated_function


# 受保护的路由，仅登录用户可见
@auth.route('/protected')  # 使用 auth.route()
@login_required
def protected():
    return '这是一个受保护的页面，仅登录用户可见。'
