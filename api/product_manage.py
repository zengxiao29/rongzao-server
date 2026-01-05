# -*- coding: utf-8 -*-
from flask import jsonify, request, g
from database import get_db_connection
from utils.auth import token_required, role_required
from utils.operation_logger import log_operation


def register_product_manage_routes(app):
    """注册商品管理相关 API 路由"""

    @app.route('/api/product-manage/search', methods=['GET'])
    @token_required
    @role_required('admin')
    def search_products():
        """搜索商品"""
        try:
            # 获取查询参数
            include = request.args.get('include', '').strip()
            exclude = request.args.get('exclude', '').strip()
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('pageSize', 50))

            # 搜索列
            search_column = request.args.get('searchColumn', 'name')  # name, alias, category, mapped_title

            # 筛选条件
            filter_no_alias = request.args.get('filterNoAlias', 'false').lower() == 'true'
            filter_no_category = request.args.get('filterNoCategory', 'false').lower() == 'true'
            filter_no_mapping = request.args.get('filterNoMapping', 'false').lower() == 'true'

            # 排序参数
            sort_column = request.args.get('sortColumn', '')  # 1=name, 2=alias, 3=category, 4=mapped_title
            sort_direction = request.args.get('sortDirection', 'asc')  # asc 或 desc

            # 计算偏移量
            offset = (page - 1) * page_size

            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                # 构建查询条件
                where_clauses = []
                params = []

                # 根据搜索列构建搜索条件
                column_map = {
                    'name': 'p.name',
                    'alias': 'p.alias',
                    'category': 'c.name',
                    'mapped_title': 'p.mapped_title'
                }
                search_field = column_map.get(search_column, 'p.name')

                # 检查是否需要JOIN CategoryInfo表
                need_join = search_field == 'c.name'

                if include:
                    where_clauses.append(f'{search_field} LIKE ?')
                    params.append(f'%{include}%')

                if exclude:
                    where_clauses.append(f'{search_field} NOT LIKE ?')
                    params.append(f'%{exclude}%')

                # 筛选条件
                if filter_no_alias:
                    where_clauses.append('(p.alias IS NULL OR p.alias = "")')

                if filter_no_category:
                    where_clauses.append('(p.category IS NULL OR p.category = 0 OR p.category = "")')

                if filter_no_mapping:
                    where_clauses.append('(p.mapped_title IS NULL OR p.mapped_title = "")')

                where_clause = 'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''

                # 构建排序子句
                order_by_clause = 'ORDER BY p.id'
                if sort_column:
                    column_map = {
                        '1': 'p.name',
                        '2': 'p.alias',
                        '3': 'c.name',
                        '4': 'p.mapped_title'
                    }
                    sort_field = column_map.get(sort_column, 'p.id')
                    sort_dir = 'ASC' if sort_direction.lower() == 'asc' else 'DESC'
                    order_by_clause = f'ORDER BY {sort_field} {sort_dir}'
                    
                    # 如果排序也使用了c.name，需要JOIN
                    if sort_field == 'c.name':
                        need_join = True

                # 查询总数
                if need_join:
                    count_sql = f'''
                        SELECT COUNT(*) as total
                        FROM ProductInfo p
                        LEFT JOIN CategoryInfo c ON p.category = c.id
                        {where_clause}
                    '''
                else:
                    count_sql = f'''
                        SELECT COUNT(*) as total
                        FROM ProductInfo p
                        {where_clause}
                    '''
                cursor.execute(count_sql, params)
                total = cursor.fetchone()['total']

                # 查询数据（关联 CategoryInfo 表）
                sql = f'''
                    SELECT 
                        p.id,
                        p.name,
                        p.alias,
                        p.category,
                        c.name as category_name,
                        p.mapped_title
                    FROM ProductInfo p
                    LEFT JOIN CategoryInfo c ON p.category = c.id
                    {where_clause}
                    {order_by_clause}
                    LIMIT ? OFFSET ?
                '''
                cursor.execute(sql, params + [page_size, offset])
                rows = cursor.fetchall()

                # 转换为字典列表
                products = []
                for row in rows:
                    products.append({
                        'id': row['id'],
                        'name': row['name'],
                        'alias': row['alias'],
                        'category': row['category'],
                        'category_name': row['category_name'],
                        'mapped_title': row['mapped_title']
                    })

                return jsonify({
                    'success': True,
                    'data': products,
                    'total': total,
                    'page': page,
                    'pageSize': page_size
                })

            finally:
                conn.close()

        except Exception as e:
            print(f'搜索商品失败: {str(e)}')
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/product-manage/categories', methods=['GET'])
    @token_required
    @role_required('admin')
    def get_categories():
        """获取所有分类列表"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                # 查询所有分类
                cursor.execute('SELECT id, name FROM CategoryInfo ORDER BY id')
                categories = cursor.fetchall()

                category_list = []
                for cat in categories:
                    category_list.append({
                        'id': cat['id'],
                        'name': cat['name']
                    })

                return jsonify({
                    'success': True,
                    'categories': category_list
                })

            finally:
                conn.close()

        except Exception as e:
            print(f'获取分类列表失败: {str(e)}')
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/product-manage/update', methods=['POST'])
    @token_required
    @role_required('admin')
    def update_product():
        """更新商品信息"""
        try:
            data = request.json
            product_id = data.get('id')
            field = data.get('field')
            value = data.get('value')

            if not product_id or not field:
                return jsonify({'error': '缺少必要参数'}), 400

            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                # 获取旧值用于日志记录
                cursor.execute('SELECT name, alias, category, mapped_title FROM ProductInfo WHERE id = ?', (product_id,))
                product = cursor.fetchone()
                
                if not product:
                    return jsonify({'error': '商品不存在'}), 404
                
                # 根据字段类型获取旧值
                old_value = None
                if field == 'alias':
                    old_value = product['alias']
                elif field == 'mapped_title':
                    old_value = product['mapped_title']
                elif field == 'category':
                    old_value = product['category']
                
                # 根据字段类型更新
                if field == 'alias':
                    # 如果值为空，设置为 NULL
                    update_value = value if value else None
                    cursor.execute('UPDATE ProductInfo SET alias = ? WHERE id = ?', (update_value, product_id))
                elif field == 'mapped_title':
                    # 如果值为空，设置为 NULL
                    update_value = value if value else None
                    cursor.execute('UPDATE ProductInfo SET mapped_title = ? WHERE id = ?', (update_value, product_id))
                elif field == 'category':
                    # value 是 category_id
                    if value and value != '':
                        # 验证分类是否存在
                        cursor.execute('SELECT id FROM CategoryInfo WHERE id = ?', (value,))
                        category_row = cursor.fetchone()
                        if category_row:
                            cursor.execute('UPDATE ProductInfo SET category = ? WHERE id = ?', (value, product_id))
                        else:
                            return jsonify({'error': '分类不存在'}), 400
                    else:
                        # 允许设置为 NULL
                        cursor.execute('UPDATE ProductInfo SET category = NULL WHERE id = ?', (product_id,))
                else:
                    return jsonify({'error': '无效的字段'}), 400

                conn.commit()

                # 记录操作日志
                log_operation(
                    username=g.current_user['username'],
                    role=g.current_user['role'],
                    operation_type=f'update_product_{field}',
                    detail={
                        'product_id': product_id,
                        'product_name': product['name'],
                        'field': field,
                        'old_value': old_value,
                        'new_value': value
                    },
                    result='success'
                )

                return jsonify({
                    'success': True,
                    'message': '更新成功'
                })

            finally:
                conn.close()

        except Exception as e:
            print(f'更新商品信息失败: {str(e)}')
            import traceback
            traceback.print_exc()
            
            # 记录失败日志
            log_operation(
                username=g.current_user['username'],
                role=g.current_user['role'],
                operation_type=f'update_product_{field}',
                detail={
                    'product_id': product_id,
                    'field': field,
                    'value': value
                },
                result='failed',
                error_message=str(e)
            )
            
            return jsonify({'error': str(e)}), 500