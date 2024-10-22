from flask import Blueprint, render_template, request, redirect, url_for, flash, session, app
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, login_required, current_user

from app import login_manager
from applications.database.database import Users # 导入你的User模型

auth = Blueprint('auth', __name__) # 创建蓝图


# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            user = Users.get(Users.username == username)  # 使用 User 模型
            print(f"User found: {user.username}")  # 调试信息

            if check_password_hash(user.password, password):  # 校验密码
                login_user(user)
                session['user_id'] = user.id  # 将用户 ID 保存到 session
                print(f"User ID in session: {session['user_id']}")  # 调试信息
                return redirect(url_for('index'))
            else:
                flash('用户名或密码错误', 'error')
                print('Password check failed')  # 调试信息
                return redirect(url_for('login'))
        except Users.DoesNotExist:  # 使用 User 模型
            flash('用户名或密码错误', 'error')
            print('User does not exist')  # 调试信息
            return redirect(url_for('login'))

    return render_template('login.html')


# 登出路由
@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)  # 清除 session 中的用户 ID
    return redirect(url_for('login'))
