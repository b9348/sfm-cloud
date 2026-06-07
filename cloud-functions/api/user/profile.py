"""
用户资料 API
GET /api/user/profile
需要 JWT 认证
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
    def do_GET(self):
        """处理 GET 请求"""
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

            # 查询用户信息
            cursor.execute(
                """SELECT id, username, created_at
                    FROM users WHERE id = %s""",
                (user_id,)
            )
            user = cursor.fetchone()

            if not user:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": False,
                    "message": "User not found"
                }).encode())
                cursor.close()
                conn.close()
                return

            # 查询用户的 Mod 数量
            cursor.execute(
                "SELECT COUNT(*) as count FROM mods WHERE author_id = %s",
                (user_id,)
            )
            mod_count = cursor.fetchone()['count']

            # 查询用户所有 Mods 的总下载量
            cursor.execute(
                """SELECT SUM(download_count) as total_downloads
                    FROM mods WHERE author_id = %s""",
                (user_id,)
            )
            result = cursor.fetchone()
            total_downloads = result['total_downloads'] or 0

            cursor.close()
            conn.close()

            # 返回成功响应
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "data": {
                    "user_id": user['id'],
                    "username": user['username'],
                    "created_at": user['created_at'].isoformat() if user['created_at'] else None,
                    "stats": {
                        "mod_count": mod_count,
                        "total_downloads": total_downloads
                    }
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
