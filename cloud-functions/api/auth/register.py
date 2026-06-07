"""
用户注册 API
POST /api/auth/register
"""
import json
import hashlib
import re
import os
import sys
import jwt
import pymysql
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """处理 POST 请求"""
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            # 验证用户名
            if not username:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "Username is required"}).encode())
                return
            
            if len(username) < 1:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "Username must be at least 1 character"}).encode())
                return
            
            if len(username) > 32:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "Username must be at most 32 characters"}).encode())
                return
            
            if not re.match(r'^[a-zA-Z0-9]+$', username):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "Username can only contain letters and numbers"}).encode())
                return
            
            # 验证密码
            if not password:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "Password is required"}).encode())
                return
            
            if len(password) < 6:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "Password must be at least 6 characters"}).encode())
                return
            
            if len(password) > 32:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "Password must be at most 32 characters"}).encode())
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
            
            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                self.send_response(409)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "Username already exists"}).encode())
                cursor.close()
                conn.close()
                return
            
            # 密码加密
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # 创建用户
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, password_hash)
            )
            conn.commit()
            user_id = cursor.lastrowid
            
            # 生成 JWT Token
            secret = os.environ.get('JWT_SECRET', 'sfm-cloud-jwt-secret-2024-secure-key')
            expire_days = int(os.environ.get('JWT_EXPIRE_DAYS', '7'))
            payload = {
                'user_id': user_id,
                'username': username,
                'exp': datetime.utcnow() + timedelta(days=expire_days),
                'iat': datetime.utcnow()
            }
            token = jwt.encode(payload, secret, algorithm='HS256')
            
            cursor.close()
            conn.close()
            
            # 返回成功响应
            self.send_response(201)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "message": "User registered successfully",
                "data": {
                    "user_id": user_id,
                    "username": username,
                    "token": token
                }
            }).encode())
            
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "message": "Invalid JSON"}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "message": str(e)}).encode())
