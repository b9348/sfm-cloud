"""
Mod 列表 API
GET /api/mods/list
支持查询参数: 
  - lang(语言): zh, en, ja, ko, ru, fr, de
  - category(分类): animation, model, texture, sound, script, other
  - search(搜索关键词): 搜索 mod_id 或多语言名称/描述
  - page(页码): 默认1
  - limit(每页数量): 默认20, 最大100
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
            search = params.get('search', [None])[0]
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
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=10,
                read_timeout=10,
                write_timeout=10
            )
            cursor = conn.cursor()

            # 构建查询条件
            where_conditions = ["m.is_public = TRUE"]
            query_params = []

            if category:
                where_conditions.append("m.category = %s")
                query_params.append(category)

            # 搜索功能 - 搜索 mod_id 或多语言内容
            if search:
                where_conditions.append("""
                    (m.mod_id LIKE %s 
                     OR m.id IN (
                         SELECT mod_id FROM mod_translations 
                         WHERE name LIKE %s OR description LIKE %s
                     ))
                """)
                search_pattern = f"%{search}%"
                query_params.extend([search_pattern, search_pattern, search_pattern])

            where_clause = " AND ".join(where_conditions)

            # 查询总数
            count_sql = f"""
                SELECT COUNT(DISTINCT m.id) as total 
                FROM mods m
                WHERE {where_clause}
            """
            cursor.execute(count_sql, query_params)
            total = cursor.fetchone()['total']

            # 查询 Mod 列表 - 优先获取指定语言，否则回退到英语
            sql = f"""
                SELECT 
                    m.id,
                    m.mod_id as mod_key,
                    m.version,
                    m.category,
                    m.download_count,
                    m.created_at,
                    m.updated_at,
                    u.username as author_name,
                    COALESCE(mt_target.name, mt_en.name, m.mod_id) as display_name,
                    COALESCE(mt_target.description, mt_en.description, '') as description,
                    CASE 
                        WHEN mt_target.name IS NOT NULL THEN %s
                        WHEN mt_en.name IS NOT NULL THEN 'en'
                        ELSE 'default'
                    END as language
                FROM mods m
                JOIN users u ON m.author_id = u.id
                LEFT JOIN mod_translations mt_target ON m.id = mt_target.mod_id AND mt_target.lang_code = %s
                LEFT JOIN mod_translations mt_en ON m.id = mt_en.mod_id AND mt_en.lang_code = 'en'
                WHERE {where_clause}
                ORDER BY m.created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql, [lang, lang] + query_params + [limit, offset])
            mods = cursor.fetchall()

            # 处理结果
            result_mods = []
            for mod in mods:
                result_mods.append({
                    "id": mod['id'],
                    "mod_key": mod['mod_key'],
                    "display_name": mod['display_name'],
                    "description": mod['description'] or '',
                    "version": mod['version'],
                    "category": mod['category'],
                    "author": mod['author_name'],
                    "download_count": mod['download_count'],
                    "language": mod['language'],
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
                        "total_pages": (total + limit - 1) // limit if total > 0 else 0
                    }
                }
            }).encode())

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"Error in mods/list: {error_detail}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "message": f"Server error: {str(e)}"
            }).encode())
