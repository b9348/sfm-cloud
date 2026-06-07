import json
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error

# 从环境变量读取配置
JWT_SECRET = os.environ.get('JWT_SECRET', 'default-secret-key')
JWT_EXPIRE_DAYS = int(os.environ.get('JWT_EXPIRE_DAYS', '7'))

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', '3306')),
    'database': os.environ.get('DB_NAME', 'sfm_cloud'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', '')
}


def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise Exception(f"数据库连接失败: {str(e)}")


def create_token(user_id: int, username: str) -> str:
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


class handler:
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body.decode('utf-8'))
            username = data.get('username', '').lower().strip()
            password = data.get('password', '')

            # 验证输入
            if not username:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "用户名不能为空"}).encode())
                return

            if len(password) < 6:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "密码长度不能少于6位"}).encode())
                return

            conn = None
            cursor = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)

                # 查询用户
                cursor.execute(
                    "SELECT id, username, password_hash FROM users WHERE username = %s AND is_active = TRUE",
                    (username,)
                )
                user = cursor.fetchone()

                if not user:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "message": "用户名或密码错误"}).encode())
                    return

                # 验证密码
                if not bcrypt.checkpw(
                    password.encode('utf-8'),
                    user['password_hash'].encode('utf-8')
                ):
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "message": "用户名或密码错误"}).encode())
                    return

                # 更新最后登录时间
                cursor.execute(
                    "UPDATE users SET last_login = NOW() WHERE id = %s",
                    (user['id'],)
                )
                conn.commit()

                token = create_token(user['id'], user['username'])

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "message": "登录成功",
                    "token": token,
                    "user_id": user['id'],
                    "username": user['username']
                }).encode())

            except Error as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": f"数据库错误: {str(e)}"}).encode())
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()

        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "message": "无效的JSON数据"}).encode())
