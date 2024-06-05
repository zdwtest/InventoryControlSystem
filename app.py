from flask import Flask, render_template, request, redirect, url_for, flash

from applications.database.database import Supplies, database, Finance, Warehouse, QualityControl, Purchase

app = Flask(__name__)


# 路由
app.secret_key = 'test'  # 必须设置密钥才能使用会话

@app.route('/login', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # 简单验证
        if username == 'admin' and password == 'secret':
            return '登录成功！'
        else:
            flash('用户名或密码错误', 'error')  # 存储错误消息
            return redirect(url_for('index'))  # 重定向回登录页面

    return render_template('login.html')

@app.route('/manage_data', methods=['GET', 'POST'])
def manage_data():
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

    return render_template('manage.html', data=data)


# --- 采购管理 ---
@app.route('/purchase_management', methods=['GET', 'POST'])
def purchase_management():
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
    return render_template('purchase_management.html', purchases=purchases)


# --- 质量监控管理 ---
@app.route('/quality_control', methods=['GET', 'POST'])
def quality_control():
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
    return render_template('quality_control.html', inspections=inspections)



# --- 出入库管理 ---
@app.route('/warehouse_management', methods=['GET', 'POST'])
def warehouse_management():
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
def finance_management():
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
def report():
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


# --- 系统管理 ---
@app.route('/system_management', methods=['GET', 'POST'])
def system_management():
    # 处理系统设置，例如用户管理、权限设置等
    # ...
    return render_template('system_management.html')


if __name__ == '__main__':

    app.run(debug=True)