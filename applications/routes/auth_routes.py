# auth_routes.py (applications/routes/auth_routes.py)

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from applications.database.database import Users

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])  # 使用 blueprint.route
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            user = Users.get(Users.username == username)
            if check_password_hash(user.password, password):
                login_user(user)
                session['user_id'] = user.id
                return redirect(url_for('index')) #  如果 index 在另一个蓝图中，需要指定蓝图名.index，例如 'main.index' 或者使用 url_for('protected.protected') 指向受保护的路由
            else:
                flash('用户名或密码错误', 'error')
                return redirect(url_for('auth.login')) # 使用蓝图名.视图函数名
        except Users.DoesNotExist:
            flash('用户名或密码错误', 'error')
            return redirect(url_for('auth.login')) # 使用蓝图名.视图函数名

    return render_template('login.html')


@auth.route('/logout')  # 使用 blueprint.route
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)
    return redirect(url_for('auth.login')) #  或者重定向到其他页面，例如 'index'