"""
删除 Mod API
DELETE /api/mods/delete
需要 JWT 认证，只能删除自己创建的 Mod
"""
import json
import os
import jwt
import pymysql
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
    def do_DELETE(self):
        """处理 DELETE 请求"""
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
            mod_id = data.get('mod_id')
            if not mod_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "Mod ID is required"
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
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=10,
                read_timeout=10,
                write_timeout=10
            )
            cursor = conn.cursor()

            # 检查 Mod 是否存在且属于当前用户
            cursor.execute(
                "SELECT id, author_id, mod_id FROM mods WHERE id = %s",
                (mod_id,)
            )
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

            if mod['author_id'] != user_id:
                self.send_response(403)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "You can only delete your own mods"
                }).encode())
                cursor.close()
                conn.close()
                return

            mod_key = mod['mod_id']

            # 删除 Mod（级联删除会自动删除关联的翻译、图片等）
            cursor.execute("DELETE FROM mods WHERE id = %s", (mod_id,))
            conn.commit()

            cursor.close()
            conn.close()

            # 返回成功响应
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "message": "Mod deleted successfully",
                "data": {
                    "mod_id": mod_id,
                    "mod_key": mod_key
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
            import traceback
            error_detail = traceback.format_exc()
            print(f"Error in mods/delete: {error_detail}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "message": f"Server error: {str(e)}"
            }).encode())
