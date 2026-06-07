"""
Mod 详情 API
GET /api/mods/{id}
支持查询参数: lang(语言)
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
            # 解析 URL 获取 mod_id
            path_parts = self.path.split('?')[0].split('/')
            mod_id = None
            for part in path_parts:
                if part.isdigit():
                    mod_id = int(part)
                    break

            if not mod_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "Invalid mod ID"
                }).encode())
                return

            # 解析查询参数
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            lang = params.get('lang', ['en'])[0]

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

            # 查询 Mod 详情 - 优先获取指定语言，否则回退到英语
            sql = """
                SELECT 
                    m.id,
                    m.mod_id as mod_key,
                    m.version,
                    m.category,
                    m.download_count,
                    m.is_public,
                    m.created_at,
                    m.updated_at,
                    u.username as author_name,
                    COALESCE(mt_target.name, mt_en.name, m.mod_id) as display_name,
                    COALESCE(mt_target.description, mt_en.description, '') as description,
                    COALESCE(mt_target.instructions, mt_en.instructions, '') as instructions,
                    COALESCE(mt_target.changelog, mt_en.changelog, '') as changelog,
                    CASE 
                        WHEN mt_target.name IS NOT NULL THEN %s
                        WHEN mt_en.name IS NOT NULL THEN 'en'
                        ELSE 'default'
                    END as language
                FROM mods m
                JOIN users u ON m.author_id = u.id
                LEFT JOIN mod_translations mt_target ON m.id = mt_target.mod_id AND mt_target.lang_code = %s
                LEFT JOIN mod_translations mt_en ON m.id = mt_en.mod_id AND mt_en.lang_code = 'en'
                WHERE m.id = %s AND m.is_public = TRUE
            """
            cursor.execute(sql, (lang, lang, mod_id))
            mod = cursor.fetchone()

            if not mod:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "Mod not found"
                }).encode())
                cursor.close()
                conn.close()
                return

            # 查询所有可用语言
            cursor.execute(
                "SELECT lang_code FROM mod_translations WHERE mod_id = %s",
                (mod_id,)
            )
            available_languages = [row['lang_code'] for row in cursor.fetchall()]

            cursor.close()
            conn.close()

            # 返回成功响应
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "data": {
                    "id": mod['id'],
                    "mod_key": mod['mod_key'],
                    "display_name": mod['display_name'],
                    "description": mod['description'] or '',
                    "instructions": mod['instructions'] or '',
                    "changelog": mod['changelog'] or '',
                    "version": mod['version'],
                    "category": mod['category'],
                    "author": mod['author_name'],
                    "download_count": mod['download_count'],
                    "language": mod['language'],
                    "available_languages": available_languages,
                    "created_at": mod['created_at'].isoformat() if mod['created_at'] else None,
                    "updated_at": mod['updated_at'].isoformat() if mod['updated_at'] else None
                }
            }).encode())

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"Error in mods/[id]: {error_detail}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "message": f"Server error: {str(e)}"
            }).encode())
