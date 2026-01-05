# -*- coding: utf-8 -*-
from flask import jsonify, request
from database import get_db_connection


def register_product_manage_routes(app):
    """注册商品管理相关 API 路由"""

    @app.route('/api/product-manage/search', methods=['GET'])
    def search_products():
        """搜索商品"""
        try:
            # 获取查询参数
            keyword = request.args.get('keyword', '').strip()
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('pageSize', 20))

            # 计算偏移量
            offset = (page - 1) * page_size

            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                # 构建查询条件
                where_clause = ''
                params = []

                if keyword:
                    where_clause = 'WHERE p.name LIKE ?'
                    params.append(f'%{keyword}%')

                # 查询总数
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
                        p.mapped_title,
                        p.reviewed
                    FROM ProductInfo p
                    LEFT JOIN CategoryInfo c ON p.category = c.id
                    {where_clause}
                    ORDER BY p.id
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
                        'mapped_title': row['mapped_title'],
                        'reviewed': row['reviewed']
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