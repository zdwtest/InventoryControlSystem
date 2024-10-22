from flask import Flask
from flask_login import LoginManager
from applications.routes.auth_routes import login,logout  # 从 auth_routes 导入蓝图
from applications.routes.protect_routes import protected
from applications.database.database import Users
# ... 其他导入

app = Flask(__name__)
# ... 配置

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # 注意这里的修改！

# ... user_loader 函数

@login_manager.user_loader
def load_user(user_id):
    try:
        return Users.get(Users.id == user_id)
    except Users.DoesNotExist:
        return None

# 注册蓝图
app.register_blueprint(login, url_prefix='/login') # 可以添加url_prefix
app.register_blueprint(logout, url_prefix='/logout') # 可以添加url_prefix



if __name__ == '__main__':
    app.run(debug=True)