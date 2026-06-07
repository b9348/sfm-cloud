"""
Mod 列表 API
GET /api/mods/list
支持查询参数: lang(语言), category(分类), page(页码), limit(每页数量)
"""
import json
import os
import pymysql
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理 GET 请求"""
        try:
            # 解析查询参数
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            # 获取参数
            lang = params.get('lang', ['en'])[0]  # 默认英语
            category = params.get('category', [None])[0]
            page = int(params.get('page', ['1'])[0])
            limit = int(params.get('limit', ['20'])[0])

            # 限制每页数量
            if limit > 100:
                limit = 100

            offset = (page - 1) * limit

            # 连接数据库
            conn = pymysql.connect(
                host=os.environ.get('DB_HOST', 'mysql7.sqlpub.com'),
                port=int(os.environ.get('DB_PORT', '3312')),
                user=os.environ.get('DB_USER', 'sfmmm1'),
                password=os.environ.get('DB_PASSWORD', 'fEPM4xyhL3WAVGYf'),
                database=os.environ.get('DB_NAME', 'sfmmm1'),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            cursor = conn.cursor()

            # 构建查询条件
            where_conditions = ["m.is_public = TRUE"]
            query_params = []

            if category:
                where_conditions.append("m.category = %s")
                query_params.append(category)

            where_clause = " AND ".join(where_conditions)

            # 查询总数
            count_sql = f"""
                SELECT COUNT(*) as total 
                FROM mods m
                WHERE {where_clause}
            """
            cursor.execute(count_sql, query_params)
            total = cursor.fetchone()['total']

            # 查询 Mod 列表
            sql = f"""
                SELECT 
                    m.id,
                    m.name,
                    m.version,
                    m.category,
                    m.download_count,
                    m.created_at,
                    m.updated_at,
                    u.username as author_name,
                    mt.display_name,
                    mt.description,
                    mt.language
                FROM mods m
                JOIN users u ON m.author_id = u.id
                LEFT JOIN mod_translations mt ON m.id = mt.mod_id AND mt.language = %s
                WHERE {where_clause}
                ORDER BY m.created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql, [lang] + query_params + [limit, offset])
            mods = cursor.fetchall()

            # 处理结果
            result_mods = []
            for mod in mods:
                result_mods.append({
                    "id": mod['id'],
                    "name": mod['name'],
                    "display_name": mod['display_name'] or mod['name'],
                    "description": mod['description'] or '',
                    "version": mod['version'],
                    "category": mod['category'],
                    "author": mod['author_name'],
                    "download_count": mod['download_count'],
                    "language": mod['language'] or lang,
                    "created_at": mod['created_at'].isoformat() if mod['created_at'] else None,
                    "updated_at": mod['updated_at'].isoformat() if mod['updated_at'] else None
                })

            cursor.close()
            conn.close()

            # 返回成功响应
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "data": {
                    "mods": result_mods,
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total": total,
                        "total_pages": (total + limit - 1) // limit
                    }
                }
            }).encode())

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"Error in mods/list: {error_detail}")  # 日志记录
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "message": f"Server error: {str(e)}"
            }).encode())
