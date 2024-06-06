from werkzeug.security import generate_password_hash
from applications.database.database import Users, database



# 检查是否已经存在管理员用户，如果不存在则创建一个
if not Users.select().where(Users.username == 'admin').exists():
    hashed_password = generate_password_hash('admin')
    user = Users.create(username='admin', password=hashed_password, is_admin=True, is_active=True)
    user.save()
    print("管理员用户创建成功！")
else:
    print("管理员用户已存在。")


