from flask import Flask
from flask_login import UserMixin
from peewee import *

app = Flask(__name__)
app.config['DATABASE'] = 'inventory.db'  # 数据库文件路径

# 创建数据库实例，所有模型都将使用此数据库
database = SqliteDatabase(app.config['DATABASE'])


# 定义基础模型，其他模型都将继承它
class BaseModel(Model):
    class Meta:
        database = database  # 设置所有子模型的数据库


# 用户模型
class Users(BaseModel, UserMixin):
    id = AutoField()
    username = CharField(unique=True)  # 用户名，唯一
    password = CharField()  # 密码
    is_admin = BooleanField(default=False)  # 是否管理员
    is_active = BooleanField(default=True)  # 是否激活
    role = IntegerField(null=True)  # 角色
    permissions = IntegerField(default=0)  # 添加permissions字段

    class Meta:
        table_name = 'users'


# 材料类别模型
class MaterialCategory(BaseModel):
    id = AutoField()
    mc = CharField()
    hh = CharField(unique=True)  # 货号(hh) 作为主键，确保唯一性
    parent_category = ForeignKeyField('self', backref='subcategories', null=True)

    class Meta:
        table_name = 'material_categories'


# 材料规格模型
class Material(BaseModel):
    id = AutoField()
    category = ForeignKeyField(MaterialCategory, backref='materials')
    mc = CharField()  # 材料名称
    ggxh = CharField(null=True)  # 规格型号 (ggxh)
    hh = CharField(unique=True)  # 货号(hh) 使用 code 作为主键，确保唯一性
    dw = CharField(null=True)  # 单位 (dw)
    kcs = DecimalField(decimal_places=2, null=False)  # 库存数量(kcs)
    pjj = DecimalField(decimal_places=2, null=True)  # 平均价(pjj)
    kczj = DecimalField(decimal_places=2, null=True)  # 库存总价(kczj)

    class Meta:
        table_name = 'materials'


# 产品类别模型
class ProductCategory(BaseModel):
    id = AutoField()
    mc = CharField()
    hh = CharField(unique=True)  # 货号(hh) 作为主键，确保唯一性
    parent_category = ForeignKeyField('self', backref='subcategories', null=True)

    class Meta:
        table_name = 'product_categories'


# 产品模型
class Product(BaseModel):
    id = AutoField()
    category = ForeignKeyField(ProductCategory, backref='products')
    mc = CharField()  # 材料名称
    ggxh = CharField(null=True)  # 规格型号 (ggxh)
    hh = CharField(unique=True)  # 货号(hh) 使用 code 作为主键，确保唯一性
    dw = CharField(null=True)  # 单位 (dw)
    kcs = DecimalField(decimal_places=2, null=False)  # 库存数量(kcs)

    class Meta:
        table_name = 'products'


# 产品用料模型
class ProductMaterial(BaseModel):
    product = ForeignKeyField(Product, backref='materials')  # 产品
    material = ForeignKeyField(Material, backref='products')  # 材料
    quantity = DecimalField(decimal_places=2)  # 数量

    class Meta:
        table_name = 'product_materials'


# 产品工序参数模型
class ProductProcessParameter(BaseModel):
    product = ForeignKeyField(Product, backref='process_parameters', primary_key=True)  # 产品，主键
    manufacturing_time = DecimalField(decimal_places=2)  # 制造工时
    galvanizing_cost = DecimalField(decimal_places=2)  # 镀锌成本
    base_material_cost = DecimalField(decimal_places=2)  # 基础材料成本

    class Meta:
        table_name = 'product_process_parameters'


# 价格预算公式模型
class ProductPriceBudgetFormula(BaseModel):
    product = ForeignKeyField(Product, backref='price_budget_formulas', primary_key=True)  # 产品，主键
    name = CharField()  # 名称
    formula = CharField()  # 公式
    description = CharField(null=True)  # 描述

    class Meta:
        table_name = 'product_price_budget_formula'

    #(1, '定额材料费', '{取定额材料费}', '来源“产品用料定制”，-产品-设置'),
    #(2, '附加材料费', '{1}*0.02', NULL),
    #(3, '镀锌费', '{取镀锌费}*1.37', '来源“产品生产工序参数设置”，-产品-设置（面积）'),
    #(4, '制造工时费', '{取制造工时费}*2', '来源“产品生产工序参数设置”，-产品-设置'),
    #(5, '合计', '{1}+{2}+{3}+{4}', NULL),
    #(6, '管理费用', '{11}*0.02/1.17', NULL),
    #(7, '销售费用', '{11}*0.03/1.17', NULL),
    #(8, '制造费用', '{11}*0.03/1.17', NULL),
    #(9, '增值税', '{11}*0.17/1.17', NULL),
    #(10, '利润', '{11}-{6}-{7}-{8}-{9}-{5}', NULL),
    #(11, '单价', '{5}/0.66', NULL);

    class Meta:
        table_name = 'product_price_budget_formulas'


# 在Flask应用上下文中创建数据库表
with app.app_context():
    database.create_tables([
        Users, MaterialCategory, Material, ProductCategory, Product, ProductMaterial, ProductProcessParameter,
        ProductPriceBudgetFormula
    ])

# 可选：测试数据库连接 (在 Flask 应用上下文中)
with app.app_context():
    try:
        Users.select().count()  # 尝试一个简单的查询
        print("数据库连接成功")
    except Exception as e:
        print(f"数据库连接失败: {e}")


# Flask应用关闭时关闭数据库连接
@app.teardown_appcontext
def close_connection(exception):
    if database:  # Check if database is initialized
        database.close()


if __name__ == '__main__':
    app.run(debug=True)
