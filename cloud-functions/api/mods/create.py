"""
创建 Mod API
POST /api/mods/create
需要 JWT 认证
"""
import json
import os
import jwt
import pymysql
from datetime import datetime
from http.server import BaseHTTPRequestHandler


def verify_token(token):
    """验证 JWT Token"""
    try:
        secret = os.environ.get('JWT_SECRET', 'sfm-cloud-jwt-secret-2024-secure-key')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token has expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """处理 POST 请求"""
        try:
            # 验证 JWT Token
            auth_header = self.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "Missing or invalid authorization header"
                }).encode())
                return

            token = auth_header.split(' ')[1]
            payload, error = verify_token(token)

            if error:
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": error
                }).encode())
                return

            user_id = payload['user_id']

            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            # 获取必填字段
            name = data.get('name', '').strip()
            display_name = data.get('display_name', '').strip()
            description = data.get('description', '').strip()
            language = data.get('language', 'en').strip()
            category = data.get('category', 'other')

            # 验证必填字段
            if not name:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "Mod name is required"
                }).encode())
                return

            if not display_name:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "Display name is required"
                }).encode())
                return

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

            # 检查 Mod 名是否已存在
            cursor.execute("SELECT id FROM mods WHERE name = %s", (name,))
            if cursor.fetchone():
                self.send_response(409)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "Mod name already exists"
                }).encode())
                cursor.close()
                conn.close()
                return

            # 创建 Mod
            cursor.execute(
                """INSERT INTO mods (author_id, name, category, is_public)
                    VALUES (%s, %s, %s, %s)""",
                (user_id, name, category, True)
            )
            conn.commit()
            mod_id = cursor.lastrowid

            # 创建多语言内容
            cursor.execute(
                """INSERT INTO mod_translations 
                    (mod_id, language, display_name, description)
                    VALUES (%s, %s, %s, %s)""",
                (mod_id, language, display_name, description)
            )
            conn.commit()

            cursor.close()
            conn.close()

            # 返回成功响应
            self.send_response(201)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "message": "Mod created successfully",
                "data": {
                    "mod_id": mod_id,
                    "name": name,
                    "display_name": display_name,
                    "language": language
                }
            }).encode())

        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "message": "Invalid JSON"
            }).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "message": str(e)
            }).encode())
