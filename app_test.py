from flask import Flask
from flask_login import LoginManager
from applications.routes.auth_routes import auth # 从 auth_routes 导入蓝图 auth
from applications.routes.protect_routes import protected # 从 protect_routes 导入蓝图 protected
from applications.database.database import Users

app = Flask(__name__)
# ... 配置

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  #  注意这里的修改，蓝图名.视图函数名

@login_manager.user_loader
def load_user(user_id):
    try:
        return Users.get(Users.id == int(user_id)) # 将 user_id 转换为整数
    except Users.DoesNotExist:
        return None

# 注册蓝图，只需注册一次 auth 蓝图
app.register_blueprint(auth, url_prefix='/auth') #  使用 url_prefix 将所有 auth 蓝图路由添加到 /auth 路径下


# 其他路由
app.register_blueprint(protected) # 如果 protected 也是蓝图

if __name__ == '__main__':
    app.run(debug=True)
