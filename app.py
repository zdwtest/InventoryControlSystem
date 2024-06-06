import os
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, get_flashed_messages
from werkzeug.security import check_password_hash

from applications.api.get_user_data import get_user_data
from applications.database.database import Supplies, database, Finance, Warehouse, QualityControl, Purchase, Users, \
    Product, Supplier
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)

# 配置 Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
# 路由
app.secret_key = os.urandom(24)  # 必须设置密钥才能使用会话

# 主页路由
from flask import render_template, redirect, url_for


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    user_data = get_user_data()
    return render_template('index.html', **user_data)


# 用户加载函数
@login_manager.user_loader
def load_user(user_id):
    try:
        return Users.get(Users.id == user_id)
    except Users.DoesNotExist:
        return None


# 管理员路由保护
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录。', 'error')
            return redirect(url_for('login'))
        elif not current_user.is_admin:
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
            user = Users.get(Users.username == username)
            print(f"User found: {user.username}")  # 调试信息

            # 确保哈希校验的逻辑正确
            if check_password_hash(user.password, password):
                login_user(user)
                session['user_id'] = user.id  # 写入 session
                print(f"User ID in session: {session['user_id']}")
                return redirect(url_for('index'))
            else:
                flash('用户名或密码错误', 'error')
                print('Password check failed')  # 调试信息
                return redirect(url_for('login'))
        except Users.DoesNotExist:
            flash('用户名或密码错误', 'error')
            print('User does not exist')  # 调试信息
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required  # 需要登录才能访问
def logout():
    logout_user()
    session.pop('user_id', None)  # 清除 session
    return redirect(url_for('login'))


@app.route('/protected')
@login_required  # 需要登录才能访问
def protected():
    return '这是一个受保护的页面，仅登录用户可见。'


@app.route('/manage_supplies', methods=['GET', 'POST'])
@login_required
def manage_data():
    # 从数据库查询当前用户的权限
    with database.atomic():  # 使用上下文管理器确保连接正确打开和关闭
        user_permissions = Users.select().where(Users.id == current_user.id).get()
        if not user_permissions.can_manage_supplies:
            # 返回权限不足的 HTML 页面
            return render_template('permissions_error.html', status=404)

        if request.method == 'POST':
            name = request.form.get('物资名称')
            spec = request.form.get('规格')
            try:
                qty = int(request.form['数量'])
            except ValueError:
                flash("数量必须是整数", 'danger')
            else:
                try:
                    # 查找是否已存在相同名称和规格的物品
                    existing_item = Supplies.get_or_none(
                        (Supplies.name == name) & (Supplies.specification == spec)
                    )

                    if existing_item:
                        # 如果存在，增加数量
                        existing_item.quantity += qty
                        existing_item.save()
                        flash("已添加数量到现有物品！", 'success')
                    else:
                        # 如果不存在，创建新物品
                        Supplies.create(name=name, specification=spec, quantity=qty)
                        flash("物资信息已成功添加！", 'success')

                except Exception as e:
                    flash(f"保存数据时出错: {e}", 'danger')

        try:
            data = Supplies.select()
        except Exception as e:
            flash(f"获取数据时出错: {e}", 'danger')
            data = []

        # 使用 Jinja2 模板渲染 HTML
        user_data = get_user_data()
    return render_template('manage_supplies.html', data=data)


# --- 采购管理 ---
@app.route('/purchase_management', methods=['GET', 'POST'])
@login_required
def purchase_management():
    # 从数据库查询当前用户的权限
    with database.atomic():  # 使用上下文管理器确保连接正确打开和关闭
        user_permissions = Users.select().where(Users.id == current_user.id).get()
        if not user_permissions.can_manage_suppliers:
            # 返回权限不足的 HTML 页面
            return render_template('permissions_error.html', status=404)
    if request.method == 'POST':
        # 1. 从表单获取数据
        material_name = request.form.get('material_name')
        supplier = request.form.get('supplier')
        quantity = int(request.form.get('quantity'))
        unit_price = float(request.form.get('unit_price'))
        total_price = quantity * unit_price
        purchase_date = request.form.get('purchase_date')

        # 2. 数据验证 (可以根据需要添加更多验证)
        if not all([material_name, supplier, quantity, unit_price, total_price, purchase_date]):
            flash("请填写所有必填字段！", 'danger')
        else:
            # 3. 创建 Purchase 对象并保存到数据库
            try:
                Purchase.create(
                    material_name=material_name,
                    supplier=supplier,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                    purchase_date=purchase_date
                )
                flash('采购订单已提交！', 'success')
                return redirect(url_for('purchase_management'))
            except Exception as e:
                flash(f"保存采购订单时出错: {e}", 'danger')

    # 获取所有采购订单数据 (用于在页面上显示)
    purchases = Purchase.select()
    user_data = get_user_data()
    return render_template('purchase_management.html', purchases=purchases)


# --- 质量监控管理 ---
@app.route('/quality_control', methods=['GET', 'POST'])
@login_required
def quality_control():
    # 从数据库查询当前用户的权限
    with database.atomic():  # 使用上下文管理器确保连接正确打开和关闭
        user_permissions = Users.select().where(Users.id == current_user.id).get()
        if not user_permissions.can_manage_quality_controls:
            # 返回权限不足的 HTML 页面
            return render_template('permissions_error.html', status=404)
    if request.method == 'POST':
        # 1. 从表单获取数据
        material_name = request.form.get('material_name')
        inspection_date = request.form.get('inspection_date')
        inspector = request.form.get('inspector')
        result = request.form.get('result')
        remarks = request.form.get('remarks')

        # 2. 数据验证 (可以根据需要添加更多验证)
        if not all([material_name, inspection_date, inspector, result]):
            flash("请填写所有必填字段！", 'danger')
        else:
            # 3. 创建 QualityControl 对象并保存到数据库
            try:
                QualityControl.create(
                    material_name=material_name,
                    inspection_date=inspection_date,
                    inspector=inspector,
                    result=result,
                    remarks=remarks
                )
                flash('质量检查记录已保存！', 'success')
                return redirect(url_for('quality_control'))
            except Exception as e:
                flash(f"保存质量检查记录时出错: {e}", 'danger')

    # 获取所有质量检查记录 (用于在页面上显示)
    inspections = QualityControl.select()
    return render_template('quality_control.html', inspections=inspections,)


# --- 出入库管理 ---
@app.route('/warehouse_management', methods=['GET', 'POST'])
@login_required
def warehouse_management():
    # 从数据库查询当前用户的权限
    with database.atomic():  # 使用上下文管理器确保连接正确打开和关闭
        user_permissions = Users.select().where(Users.id == current_user.id).get()
        if not user_permissions.can_manage_warehouses:
            # 返回权限不足的 HTML 页面
            return render_template('permissions_error.html', status=404)
    if request.method == 'POST':
        # 1. 确定操作类型 (入库/出库)
        operation_type = request.form.get('operation_type')

        # 2. 从表单获取数据
        material_name = request.form.get('material_name')
        quantity = int(request.form.get('quantity'))
        date = request.form.get('date')

        # 3. 数据验证 (可以根据需要添加更多验证)
        if not all([material_name, quantity, date]):
            flash("请填写所有必填字段！", 'danger')
        else:
            # 4. 更新库存记录 (Warehouse 模型)
            try:
                # 查找 existing_item 的逻辑
                existing_item = Warehouse.get_or_none(Warehouse.material_name)

                if operation_type == 'in':
                    if existing_item:
                        existing_item.quantity += quantity
                    else:
                        Warehouse.create(
                            material_name=material_name,
                            quantity=quantity
                        )
                    flash('入库操作已完成！', 'success')
                elif operation_type == 'out':
                    if existing_item:
                        if existing_item.quantity >= quantity:
                            existing_item.quantity -= quantity
                            flash('出库操作已完成！', 'success')
                        else:
                            flash('出库数量超过库存！', 'danger')
                    else:
                        flash('没有找到对应的库存记录！', 'danger')
                else:
                    flash('无效的操作类型！', 'danger')

                if existing_item:
                    existing_item.save()
                return redirect(url_for('warehouse_management'))

            except Exception as e:
                flash(f"出入库操作时出错: {e}", 'danger')

    # 获取库存信息 (用于在页面上显示)
    inventory = Warehouse.select()
    return render_template('warehouse_management.html', inventory=inventory)


# --- 财务管理 ---
@app.route('/finance_management', methods=['GET', 'POST'])
@login_required
def finance_management():
    # 从数据库查询当前用户的权限
    with database.atomic():  # 使用上下文管理器确保连接正确打开和关闭
        user_permissions = Users.select().where(Users.id == current_user.id).get()
        if not user_permissions.can_manage_finances:
            # 返回权限不足的 HTML 页面
            return render_template('permissions_error.html', status=404)
    if request.method == 'POST':
        # 1. 从表单获取数据
        transaction_type = request.form.get('transaction_type')
        amount = float(request.form.get('amount'))
        date = request.form.get('date')
        description = request.form.get('description')

        # 2. 数据验证 (可以根据需要添加更多验证)
        if not all([transaction_type, amount, date]):
            flash("请填写所有必填字段！", 'danger')
        else:
            # 3. 创建/更新 Finance 对象并保存到数据库
            try:
                Finance.create(
                    transaction_type=transaction_type,
                    amount=amount,
                    date=date,
                    description=description
                )
                flash('财务记录已更新！', 'success')
                return redirect(url_for('finance_management'))
            except Exception as e:
                flash(f"更新财务记录时出错: {e}", 'danger')

    # 获取财务信息 (用于在页面上显示)
    transactions = Finance.select()
    return render_template('finance_management.html', transactions=transactions)


# --- 统计报表 ---
@app.route('/report', methods=['GET'])
@login_required
def report():
    # 从数据库查询当前用户的权限
    with database.atomic():  # 使用上下文管理器确保连接正确打开和关闭
        user_permissions = Users.select().where(Users.id == current_user.id).get()
        if not user_permissions.can_manage_reports:
            # 返回权限不足的 HTML 页面
            return render_template('permissions_error.html', status=404)
    # --- 物资统计 ---
    supplies_data = Supplies.select()
    total_supplies_value = 0
    for item in supplies_data:
        total_supplies_value += item.quantity  # 假设价值等同于数量，你需要根据实际情况修改

    # --- 采购统计 ---
    purchases_data = Purchase.select()
    total_purchase_amount = sum(purchase.total_price for purchase in purchases_data)

    # --- 财务统计 ---
    finance_data = Finance.select()
    total_income = sum(transaction.amount for transaction in finance_data if transaction.transaction_type == 'income')
    total_expenses = sum(
        transaction.amount for transaction in finance_data if transaction.transaction_type == 'expense')
    net_profit = total_income - total_expenses

    return render_template('report.html',
                           supplies_data=supplies_data,
                           total_supplies_value=total_supplies_value,
                           purchases_data=purchases_data,
                           total_purchase_amount=total_purchase_amount,
                           total_income=total_income,
                           total_expenses=total_expenses,
                           net_profit=net_profit)

# 管理供应商路由
@app.route('/manage_suppliers', methods=['GET', 'POST'])
@login_required
def manage_suppliers():
    # 从数据库查询当前用户的权限
    with database.atomic():  # 使用上下文管理器确保连接正确打开和关闭
        user_permissions = Users.select().where(Users.id == current_user.id).get()
        if not user_permissions.can_manage_suppliers:
            # 返回权限不足的 HTML 页面
            return render_template('permissions_error.html', status=404)

    if request.method == 'POST':
        # 获取表单数据
        name = request.form.get('name')
        contact_person = request.form.get('contact_person')
        phone = request.form.get('phone')
        address = request.form.get('address')

        # 验证数据
        if not all([name, contact_person, phone, address]):
            flash("请填写所有必填字段！", 'danger')
        else:
            # 创建供应商对象并保存到数据库
            try:
                Supplier.create(
                    name=name,
                    contact_person=contact_person,
                    phone=phone,
                    address=address
                )
                flash("供应商信息已成功添加！", 'success')
                return redirect(url_for('manage_suppliers'))
            except Exception as e:
                flash(f"保存供应商信息时出错: {e}", 'danger')

    # 获取所有供应商数据 (用于在页面上显示)
    suppliers = Supplier.select()
    return render_template('manage_suppliers.html', suppliers=suppliers)

# 管理产品路由
@app.route('/manage_products', methods=['GET', 'POST'])
@login_required
def manage_products():
    # 从数据库查询当前用户的权限
    with database.atomic():  # 使用上下文管理器确保连接正确打开和关闭
        user_permissions = Users.select().where(Users.id == current_user.id).get()
        if not user_permissions.can_manage_products:
            # 返回权限不足的 HTML 页面
            return render_template('permissions_error.html', status=404)

    if request.method == 'POST':
        # 获取表单数据
        name = request.form.get('name')
        description = request.form.get('description')
        unit = request.form.get('unit')
        price = request.form.get('price')

        # 验证数据
        if not all([name, description, unit, price]):
            flash("请填写所有必填字段！", 'danger')
        else:
            # 创建产品对象并保存到数据库
            try:
                Product.create(
                    name=name,
                    description=description,
                    unit=unit,
                    price=price
                )
                flash("产品信息已成功添加！", 'success')
                return redirect(url_for('manage_products'))
            except Exception as e:
                flash(f"保存产品信息时出错: {e}", 'danger')

    # 获取所有产品数据 (用于在页面上显示)
    products = Product.select()
    return render_template('manage_products.html', products=products)

# 系统管理视图
@app.route('/system_management', methods=['GET', 'POST'])
@login_required
@admin_required
def system_management():
    users = Users.select()
    return render_template('system_management.html', users=users)


# 编辑用户权限视图
@app.route('/edit_user_permissions/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user_permissions(user_id):
    user = Users.get_or_none(Users.id == user_id)
    if not user:
        abort(404)

    if request.method == 'POST':
        user.can_manage_users = 'can_manage_users' in request.form
        user.can_manage_supplies = 'can_manage_supplies' in request.form
        user.can_manage_suppliers = 'can_manage_suppliers' in request.form
        user.can_manage_products = 'can_manage_products' in request.form
        user.can_manage_purchases = 'can_manage_purchases' in request.form
        user.can_manage_quality_controls = 'can_manage_quality_controls' in request.form
        user.can_manage_warehouses = 'can_manage_warehouses' in request.form
        user.can_manage_finances = 'can_manage_finances' in request.form
        user.save()
        return redirect(url_for('system_management'))

    return render_template('edit_user_permissions.html', user=user)


if __name__ == '__main__':
    app.run(debug=True)
