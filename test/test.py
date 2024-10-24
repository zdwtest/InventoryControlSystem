# 管理产品规格路由
@app.route('/products', defaults={'page': 1, 'q': ''})
@app.route('/products/<int:page>', defaults={'q': ''})
@app.route('/products/<int:page>/<string:q>')
@login_required
def view_products(page, q):
    """显示物料列表，包含分页和搜索功能。"""
    try:
        per_page = 10
        page = max(1, page)

        query = product.select().join(productCategory)

        if q:
            search_terms = q.split()
            for term in search_terms:
                query = query.where(
                    (product.mc.contains(term)) |
                    (product.ggxh.contains(term)) |
                    (product.hh.contains(term)) |
                    (productCategory.mc.contains(term))
                )

        total = query.count()
        offset = (page - 1) * per_page
        products = (query
                     .order_by(product.id)
                     .offset(offset)
                     .limit(per_page)
                     .objects()
                     )

        total_pages = (total + per_page - 1) // per_page

        return render_template('products.html', products=products,
                               current_page=page, total_pages=total_pages, per_page=per_page,
                               q=q,
                               max=max, min=min,
                               user_data=get_user_data())

    except Exception as e:
        print(f"Error in view_products: {e}")
        return render_template('index.html', error_message="加载物料时发生错误"), 500



# 管理产品规格路由 (新增和修改)
@app.route('/products/manage', methods=['GET', 'POST'])
@app.route('/products/manage/<int:product_id>', methods=['GET', 'POST'])  # 允许编辑已有记录
@login_required
def manage_products(product_id=None):
    user_data = get_user_data()
    if not has_permission(current_user, PERMISSION_MANAGE_products):
        flash('您没有权限管理产品规格。', 'error')
        return redirect(url_for('products'))

    categories = productCategory.select()
    product = product.get_or_none(product.id == product_id) if product_id else None

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
                raise ValueError("产品名称、货号和库存数量不能为空")
            try:
                kcs = float(kcs)
                if kcs < 0:
                    raise ValueError("库存数量不能为负数")
            except ValueError:
                raise ValueError("库存数量必须是数字")

            if product:
                product.category = productCategory.get(productCategory.id == category_id)
                product.mc = mc
                product.ggxh = ggxh
                product.hh = hh
                product.dw = dw
                product.kcs = kcs
                product.pjj = float(pjj) if pjj else None
                product.kczj = float(kczj) if kczj else None
                product.save()
                flash('产品规格修改成功!', 'success')
            else:
                new_product = product.create(
                    category=productCategory.get(productCategory.id == category_id),
                    mc=mc,
                    ggxh=ggxh,
                    hh=hh,
                    dw=dw,
                    kcs=kcs,
                    pjj=float(pjj) if pjj else None,
                    kczj=float(kczj) if kczj else None,
                )
                flash('产品规格添加成功!', 'success')

        except productCategory.DoesNotExist:
            flash("选择的类别不存在", 'error')
        except Exception as e:
            database.rollback()
            flash(f'操作失败: {e}', 'error')
            return render_template('products_manage.html', product=product, categories=categories, **user_data)

    return render_template('products_manage.html', product=product, categories=categories, **user_data)


# 删除产品规格路由
@app.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    if not has_permission(current_user, PERMISSION_MANAGE_products):
        flash('您没有权限删除产品规格。', 'error')
        return redirect(url_for('view_products'))

    product = product.get_or_none(product.id == product_id)
    if product:
        try:
            product.delete_instance()
            flash('产品规格删除成功!', 'success')
        except Exception as e:
            flash(f'删除失败: {e}', 'error')
    else:
        flash('产品规格不存在', 'error')
    return redirect(url_for('products'))