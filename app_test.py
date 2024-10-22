import json
import os
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from select import select
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from applications.api.get_user_data import get_user_data
from applications.database.database import database, Users, \
    MaterialCategory, Material, ProductCategory, \
    Product, ProductPriceBudgetFormula, \
    ProductMaterial, ProductProcessParameter  # 导入数据库模型

app = Flask(__name__)
app.secret_key = os.urandom(24)


# Flask-Login 设置
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    try:
        return Users.get(Users.id == user_id)
    except Users.DoesNotExist:
        return None


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


# --- 路由 ---

@app.route('/')
@login_required
def index():
    user_data = get_user_data()
    return render_template('index.html', **user_data)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            user = Users.get(Users.username == username)
            if check_password_hash(user.password, password):  # 检查哈希密码
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('用户名或密码错误', 'error')
        except Users.DoesNotExist:
            flash('用户名或密码错误', 'error')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ... (其他路由，例如 manage_supplies, purchase_management 等)


# 管理材料规格路由
@app.route('/materials', methods=['GET', 'POST'])
@login_required
def manage_materials():  # 函数名更正为 manage_materials
    if current_user.role != 1:  # 使用 current_user 并直接比较 role 值
        flash('您没有权限访问此页面。', 'error')
        return redirect(url_for('index'))

    return render_template('materials.html')





# 系统管理路由
@app.route('/edit_user_permissions', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user_permissions():
    if request.method == 'POST':
        try:
            user_id = request.form.get('user_id')
            user = Users.get(Users.id == user_id)

            if 'update_role' in request.form:
                selected_roles = request.form.getlist('role')
                user.role = ",".join(map(str, selected_roles))  # 使用逗号连接角色
                user.save()
                flash('用户角色已更新。', 'success')

            elif 'toggle_active' in request.form:
                user.is_active = not user.is_active
                user.save()
                flash(f"用户 {user.username} 已{'禁用' if not user.is_active else '启用'}。", 'success')

            elif 'toggle_admin' in request.form:
                user.is_admin = not user.is_admin
                user.save()
                flash(f"用户 {user.username} 的管理员权限已{'移除' if not user.is_admin else '授予'}。", 'success')

        except (Users.DoesNotExist, ValueError, TypeError) as e:
            print(e) # 打印错误信息，方便调试
            flash('操作失败。', 'danger')
        return redirect(url_for('edit_user_permissions'))  # 重定向

    users = Users.select()
    available_roles = [0, 1, 2, 3, 4]# 可用角色
    roles_dict = {
        0: '普通员工',
        1: '设计部门负责人',
        2: '生产部门负责人',
        3: '仓库管理员',
        4: '车间领料人'
    }
    for user in users:
        try:
            user.role = [int(r.strip()) for r in user.role.split(',') if
                         r.strip()]  # 将角色字符串转换为整数列表
        except (ValueError, AttributeError):
            user.role = []  # 如果无法转换，则将角色设置为空列表

    return render_template('edit_user_permissions.html', users=users, available_roles=available_roles,
                           roles=roles_dict)  # 渲染模板
if __name__ == '__main__':
    app.run(debug=True)