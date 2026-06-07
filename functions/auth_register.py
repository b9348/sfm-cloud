"""
用户注册 API
POST /auth/register
"""
import json
import hashlib
import re
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(__file__))

# 导入共享模块
from utils import create_db_connection, validate_username, validate_password, generate_jwt

class handler:
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
            is_valid, error_msg = validate_username(username)
            if not is_valid:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": error_msg}).encode())
                return
            
            # 验证密码
            is_valid, error_msg = validate_password(password)
            if not is_valid:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": error_msg}).encode())
                return
            
            # 连接数据库
            conn = create_db_connection()
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
            token = generate_jwt(user_id, username)
            
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
