import os
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, get_flashed_messages
from werkzeug.security import check_password_hash

from applications.api.get_user_data import get_user_data
from applications.database.database import Users, MaterialCategory, Material, ProductCategory, Product, ProductMaterial  # 导入所有模型
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)

# 配置 Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # 设置登录页面的路由

# 设置 Flask 的密钥，用于 session 加密
app.secret_key = os.urandom(24)

# --- 路由 ---

# 主页路由
@app.route('/', methods=['GET', 'POST'])
@login_required  # 需要登录才能访问
def index():
    user_data = get_user_data()
    return render_template('index.html', **user_data)


# 用户加载函数，用于 Flask-Login
@login_manager.user_loader
def load_user(user_id):
    try:
        return Users.get(Users.id == user_id)  # 使用 User 模型
    except Users.DoesNotExist:
        return None


# 管理员权限装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录。', 'error')
            return redirect(url_for('login'))
        elif not current_user.is_admin:  # 检查用户是否为管理员
            flash('您没有权限访问此页面。', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function


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


# 受保护的路由，仅登录用户可见
@app.route('/protected')
@login_required
def protected():
    return '这是一个受保护的页面，仅登录用户可见。'




if __name__ == '__main__':
    app.run(debug=True)