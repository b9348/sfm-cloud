"""
Mod 详情 API
GET /api/mods/{id}
"""
import json
import os
import pymysql
import re
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理 GET 请求"""
        try:
            # 解析 URL 获取 mod_id
            # self.path 格式: /api/mods/123?lang=en
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
                cursorclass=pymysql.cursors.DictCursor
            )
            cursor = conn.cursor()

            # 查询 Mod 详情
            sql = """
                SELECT 
                    m.id,
                    m.name,
                    m.version,
                    m.category,
                    m.download_count,
                    m.is_public,
                    m.created_at,
                    m.updated_at,
                    u.username as author_name,
                    mt.display_name,
                    mt.description,
                    mt.instructions,
                    mt.changelog,
                    mt.language
                FROM mods m
                JOIN users u ON m.author_id = u.id
                LEFT JOIN mod_translations mt ON m.id = mt.mod_id AND mt.language = %s
                WHERE m.id = %s AND m.is_public = TRUE
            """
            cursor.execute(sql, (lang, mod_id))
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

            # 查询图片
            cursor.execute(
                "SELECT image_url FROM mod_images WHERE mod_id = %s ORDER BY sort_order",
                (mod_id,)
            )
            images = [row['image_url'] for row in cursor.fetchall()]

            # 查询依赖
            cursor.execute("""
                SELECT m.id, m.name, mt.display_name
                FROM mod_dependencies md
                JOIN mods m ON md.dependency_mod_id = m.id
                LEFT JOIN mod_translations mt ON m.id = mt.mod_id AND mt.language = %s
                WHERE md.mod_id = %s
            """, (lang, mod_id))
            dependencies = []
            for dep in cursor.fetchall():
                dependencies.append({
                    "id": dep['id'],
                    "name": dep['name'],
                    "display_name": dep['display_name'] or dep['name']
                })

            # 查询文件
            cursor.execute(
                "SELECT file_url, file_name, file_size, version FROM mod_files WHERE mod_id = %s",
                (mod_id,)
            )
            files = []
            for file in cursor.fetchall():
                files.append({
                    "url": file['file_url'],
                    "name": file['file_name'],
                    "size": file['file_size'],
                    "version": file['version']
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
                    "id": mod['id'],
                    "name": mod['name'],
                    "display_name": mod['display_name'] or mod['name'],
                    "description": mod['description'] or '',
                    "instructions": mod['instructions'] or '',
                    "changelog": mod['changelog'] or '',
                    "version": mod['version'],
                    "category": mod['category'],
                    "author": mod['author_name'],
                    "download_count": mod['download_count'],
                    "language": mod['language'] or lang,
                    "images": images,
                    "dependencies": dependencies,
                    "files": files,
                    "created_at": mod['created_at'].isoformat() if mod['created_at'] else None,
                    "updated_at": mod['updated_at'].isoformat() if mod['updated_at'] else None
                }
            }).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "message": str(e)
            }).encode())
