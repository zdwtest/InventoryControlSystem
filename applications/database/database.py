from flask_login import UserMixin
from peewee import MySQLDatabase, Model, CharField, IntegerField, ForeignKeyField, DecimalField, DateField, TextField, \
    BooleanField
from flask import Flask

app = Flask(__name__)
app.config['DATABASE'] = {
    'user': 'Inventory',
    'password': 'd4iSGSa7KYc7SMm3',
    'host': '162.251.92.166',
    'port': 3306
}

database = MySQLDatabase('Inventory', **app.config['DATABASE'])


# 用户模型
class Users(Model, UserMixin):
    id = IntegerField(primary_key=True)
    username = CharField(unique=True)
    password = CharField()
    is_admin = BooleanField(default=False)  # 是否是管理员
    is_active = BooleanField(default=True)  # 用户是否被禁用

    class Meta:
        database = database


class Supplies(Model):
    name = CharField()
    specification = CharField()
    quantity = IntegerField()

    class Meta:
        database = database


# --- 供应商模型 (为 Purchase 模型添加关联) ---
class Supplier(Model):
    name = CharField()
    contact_person = CharField()
    phone = CharField()
    address = CharField()

    class Meta:
        database = database


# --- 产品模型 (为多个模型添加关联) ---
class Product(Model):
    name = CharField()
    description = TextField()
    unit = CharField()  # 单位，例如：个、箱、米
    price = DecimalField(decimal_places=2)

    class Meta:
        database = database


# --- 采购模型 ---
class Purchase(Model):
    supplier = ForeignKeyField(Supplier, backref='purchases')  # 供应商
    product = ForeignKeyField(Product, backref='purchases')  # 产品
    quantity = IntegerField()
    total_price = DecimalField(decimal_places=2)
    purchase_date = DateField()  # 采购日期

    # 可以添加其他字段，例如：
    # purchase_order_number = CharField()  # 采购订单号
    # status = CharField()  # 采购状态 (例如：已下单、已到货、已完成)

    class Meta:
        database = database


# --- 质量监控模型 ---
class QualityControl(Model):
    purchase = ForeignKeyField(Purchase, backref='quality_controls')  # 关联采购订单
    inspection_date = DateField()  # 质检日期
    inspector = CharField()  # 质检员
    result = CharField()  # 质检结果 (例如：合格、不合格)

    # 可以添加其他字段，例如：
    # defects = TextField()  # 缺陷描述
    # remarks = TextField()  # 备注

    class Meta:
        database = database


# --- 仓库模型 ---
class Warehouse(Model):
    material_name = CharField()
    product = ForeignKeyField(Product, backref='warehouse_entries')  # 产品
    quantity = IntegerField()  # 库存数量
    location = CharField()  # 库位

    # 可以添加其他字段，例如：
    # last_in_date = DateField()  # 最后入库日期
    # last_out_date = DateField()  # 最后出库日期

    class Meta:
        database = database


# --- 财务模型 ---
class Finance(Model):
    date = DateField()  # 财务记录日期
    type = CharField()  # 类型 (例如：收入、支出)
    amount = DecimalField(decimal_places=2)
    description = TextField()

    # 可以添加其他字段，例如：
    # related_model = CharField()  # 关联的模型，例如：采购、销售等
    # related_id = IntegerField()  # 关联的模型的 ID

    class Meta:
        database = database


# 在应用启动时创建表格
with app.app_context():
    try:
        database.connect()
        database.create_tables([
            Users,
            Supplies,
            Supplier,  # 确保 Supplier 在 Purchase 之前创建
            Product,  # 将 Product 添加到此处
            Purchase,
            QualityControl,
            Warehouse,
            Finance  # 添加Finance模型
        ])
        print("数据库连接成功！已创建表格。")
    except Exception as e:
        print(f"数据库连接或表格创建失败：{e}")


@app.teardown_appcontext
def close_connection(exception):
    database.close()


if __name__ == '__main__':
    app.run(debug=True)
