from flask_login import UserMixin
from peewee import SqliteDatabase, Model, CharField, IntegerField, ForeignKeyField, DecimalField, DateField, TextField, \
    BooleanField, AutoField

from flask import Flask

app = Flask(__name__)
app.config['DATABASE'] = 'inventory.db'  # 直接指定数据库文件路径

database = SqliteDatabase(app.config['DATABASE']) # 使用 SqliteDatabase 并传入文件路径

class Users(Model, UserMixin):
    id = AutoField()  # 使用 AutoField 实现自增主键
    username = CharField(unique=True)
    password = CharField()
    is_admin = BooleanField(default=False)
    is_active = BooleanField(default=True)
    # --- 权限字段 ---
    role = CharField(null=True)

    class Meta:
        database = SqliteDatabase('inventory.db')


class MaterialCategory(Model): # 材料类别表
    id = AutoField()
    name = CharField()
    parent_category = ForeignKeyField('self', backref='subcategories', null=True) # 支持多级分类

    class Meta:
        database = database
        table_name = 'material_categories'


class Material(Model): # 材料表
    id = AutoField()
    category = ForeignKeyField(MaterialCategory, backref='materials')
    name = CharField()
    specification = CharField()  # 规格型号

    class Meta:
        database = database
        table_name = 'materials'


class ProductCategory(Model): # 产品类别表，结构类似材料类别
    id = AutoField()
    name = CharField()
    parent_category = ForeignKeyField('self', backref='subcategories', null=True)

    class Meta:
        database = database
        table_name = 'product_categories'



class Product(Model):
    id = AutoField()
    category = ForeignKeyField(ProductCategory, backref='products')
    name = CharField()
    description = TextField()
    unit = CharField()
    price = DecimalField(decimal_places=2)

    class Meta:
        database = database
        table_name = 'products'


class ProductMaterial(Model): # 产品用料表
    product = ForeignKeyField(Product, backref='materials')
    material = ForeignKeyField(Material, backref='products')
    quantity = IntegerField()

    class Meta:
        database = database
        table_name = 'product_materials'




with app.app_context():
    try:
        Users.select().count()  # 尝试一个简单的查询
        print("数据库连接成功")
    except Exception as e:
        print(f"数据库连接失败: {e}")

# 创建表格
with app.app_context():
    database.create_tables([
        Users,
        MaterialCategory,
        Material,
        ProductCategory,
        Product,
        ProductMaterial,
    ]) # 注意这里有闭合的 ]
    print("表格创建成功")


@app.teardown_appcontext
def close_connection(exception):
    database.close()


if __name__ == '__main__':
    app.run(debug=True)
