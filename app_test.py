import json
import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from peewee import IntegrityError
from select import select
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, user_unauthorized, \
    user_accessed

from applications.api.get_user_data import get_user_data
from applications.database.database import database, Users, \
    MaterialCategory, Material, ProductCategory, \
    Product, ProductPriceBudgetFormula, \
    ProductMaterial, ProductProcessParameter  # 导入数据库模型

app = Flask(__name__)
app.secret_key = os.urandom(24)


# Flask-Login 设置
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

PERMISSION_VIEW = 0x1
PERMISSION_MANAGE_MATERIALS = 0x2
PERMISSION_VIEW_USERS = 0x4
PERMISSION_MANAGE_USERS = 0x8
PERMISSION_VIEW_REPORTS = 0x10
PERMISSION_MANAGE_REPORTS = 0x20

roles_dict = {
    PERMISSION_VIEW: '普通员工',  # Map permissions to roles
    PERMISSION_MANAGE_MATERIALS: '设计部门负责人',
    PERMISSION_VIEW_USERS: '生产部门负责人',
    PERMISSION_MANAGE_USERS: '仓库管理员',
    PERMISSION_VIEW_REPORTS: '车间领料人'  # Add additional roles as needed
}


@login_manager.user_loader
def load_user(user_id):
    try:
        return Users.get(Users.id == user_id,Users.is_active == user_accessed,
                         )

    except Users.DoesNotExist:
        return None


# 管理员装饰器
def admin_required(func):
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated and current_user.is_admin:  # 只检查 is_admin
            return func(*args, **kwargs)
        else:
            flash('您没有权限访问此页面。', 'danger')
            return redirect(url_for('index'))

    wrapper.__name__ = func.__name__
    return wrapper


# --- 路由 ---

@app.route('/')
@login_required
def index():
    user_data = get_user_data()
    return render_template('index.html', **user_data)


@app.route('/login', methods=['GET', 'POST'])
def login():
    user_data = get_user_data()
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            user = Users.get(Users.username == username)
            if check_password_hash(user.password, password):  # 检查哈希密码
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('用户名或密码错误', 'error')
        except Users.DoesNotExist:
            flash('用户名或密码错误', 'error')
    return render_template('login.html',**user_data)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# 测试用户角色路由
@app.route('/test_user_roles')
@login_required
def test_user_roles():
    user_data = get_user_data()
    print(user_data)
    return render_template('test_user_roles.html', **user_data)

# 管理材料规格路由
@app.route('/materials', defaults={'page': 1, 'q': ''})
@app.route('/materials/<int:page>', defaults={'q': ''})
@app.route('/materials/<int:page>/<string:q>')
@login_required
def view_materials(page, q):
    """显示物料列表，包含分页和搜索功能。"""
    try:
        per_page = 10
        page = max(1, page)

        query = Material.select().join(MaterialCategory)

        if q:
            search_terms = q.split()
            for term in search_terms:
                query = query.where(
                    (Material.mc.contains(term)) |
                    (Material.ggxh.contains(term)) |
                    (Material.hh.contains(term)) |
                    (MaterialCategory.mc.contains(term))
                )

        total = query.count()
        offset = (page - 1) * per_page
        materials = (query
                     .order_by(Material.id)
                     .offset(offset)
                     .limit(per_page)
                     .objects()
                     )

        total_pages = (total + per_page - 1) // per_page

        return render_template('materials.html', materials=materials,
                               current_page=page, total_pages=total_pages, per_page=per_page,
                               q=q,
                               max=max, min=min,
                               user_data=get_user_data())

    except Exception as e:
        print(f"Error in view_materials: {e}")
        return render_template('index.html', error_message="加载物料时发生错误"), 500



# 管理材料规格路由 (新增和修改)
@app.route('/materials/manage', methods=['GET', 'POST'])
@app.route('/materials/manage/<int:material_id>', methods=['GET', 'POST'])  # 允许编辑已有记录
@login_required
def manage_materials(material_id=None):
    user_data = get_user_data()
    if not has_permission(current_user, PERMISSION_MANAGE_MATERIALS):
        flash('您没有权限管理材料规格。', 'error')
        return redirect(url_for('materials'))

    categories = MaterialCategory.select()
    material = Material.get_or_none(Material.id == material_id) if material_id else None

    if request.method == 'POST':
        try:
            category_id = int(request.form['category'])
            mc = request.form['mc']
            ggxh = request.form['ggxh']
            hh = request.form['hh']
            dw = request.form['dw']
            kcs = request.form['kcs']
            pjj = request.form['pjj']
            kczj = request.form['kczj']

            # 数据验证
            if not mc or not hh or not kcs:
                raise ValueError("材料名称、货号和库存数量不能为空")
            try:
                kcs = float(kcs)
                if kcs < 0:
                    raise ValueError("库存数量不能为负数")
            except ValueError:
                raise ValueError("库存数量必须是数字")

            if material:
                material.category = MaterialCategory.get(MaterialCategory.id == category_id)
                material.mc = mc
                material.ggxh = ggxh
                material.hh = hh
                material.dw = dw
                material.kcs = kcs
                material.pjj = float(pjj) if pjj else None
                material.kczj = float(kczj) if kczj else None
                material.save()
                flash('材料规格修改成功!', 'success')
            else:
                new_material = Material.create(
                    category=MaterialCategory.get(MaterialCategory.id == category_id),
                    mc=mc,
                    ggxh=ggxh,
                    hh=hh,
                    dw=dw,
                    kcs=kcs,
                    pjj=float(pjj) if pjj else None,
                    kczj=float(kczj) if kczj else None,
                )
                flash('材料规格添加成功!', 'success')

        except MaterialCategory.DoesNotExist:
            flash("选择的类别不存在", 'error')
        except Exception as e:
            database.rollback()
            flash(f'操作失败: {e}', 'error')
            return render_template('materials_manage.html', material=material, categories=categories, **user_data)

    return render_template('materials_manage.html', material=material, categories=categories, **user_data)


# 删除材料规格路由
@app.route('/materials/<int:material_id>/delete', methods=['POST'])
@login_required
def delete_material(material_id):
    if not has_permission(current_user, PERMISSION_MANAGE_MATERIALS):
        flash('您没有权限删除材料规格。', 'error')
        return redirect(url_for('view_materials'))

    material = Material.get_or_none(Material.id == material_id)
    if material:
        try:
            material.delete_instance()
            flash('材料规格删除成功!', 'success')
        except Exception as e:
            flash(f'删除失败: {e}', 'error')
    else:
        flash('材料规格不存在', 'error')
    return redirect(url_for('materials'))



# 系统管理路由
@app.route('/edit_user_permissions', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user_permissions():
    if request.method == 'POST':
        try:
            with database.atomic():
                user_id = request.form.get('user_id')
                user = Users.get(Users.id == user_id)

                if request.form.get('selectAll') == '1':
                    selected_roles = sum("0")
                else:
                    selected_roles = [int(r, 16) for r in request.form.getlist('role')]

                user.permissions = user.permissions | sum(selected_roles)
                user.save()
                flash('用户角色已更新。', 'success')

        except (Users.DoesNotExist, ValueError, TypeError, IntegrityError) as e:
            flash(f'操作失败: {e}', 'danger')
            print(f"更新用户权限失败: {e}")
        return redirect(url_for('edit_user_permissions'))


    users = Users.select()
    available_roles = [0x1, 0x2, 0x4, 0x8, 0x10]
    roles_dict = {
        0x1: '普通员工',
        0x2: '材料管理负责人',
        0x4: '产品管理负责人',
        0x8: '仓库管理员',
        0x10: '车间领料人'
    }

    return render_template('edit_user_permissions.html', users=users, available_roles=available_roles, roles=roles_dict)

#权限检查函数 (添加到你的代码中)
def has_permission(user, permission):
    return (user.permissions & permission) == permission

# 注册自定义 Jinja2 过滤器
@app.template_filter('check_permission')
def check_permission(permissions, role):
    return (permissions & role) != 0

if __name__ == '__main__':
    app.run(debug=True)