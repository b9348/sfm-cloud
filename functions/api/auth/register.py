from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, validator
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error

app = FastAPI()

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


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=32, pattern=r'^[a-zA-Z0-9]+$')
    password: str = Field(..., min_length=6, max_length=32)

    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v.lower()


class RegisterResponse(BaseModel):
    success: bool
    message: str
    token: str = None
    user_id: int = None


def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise HTTPException(status_code=500, detail=f"数据库连接失败: {str(e)}")


def create_token(user_id: int, username: str) -> str:
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


@app.post("/api/auth/register")
async def register(request: Request):
    data = await request.json()
    username = data.get('username', '').lower()
    password = data.get('password', '')

    # 验证输入
    if not username or not username.isalnum():
        return RegisterResponse(success=False, message="用户名只能包含字母和数字")
    if len(password) < 6 or len(password) > 32:
        return RegisterResponse(success=False, message="密码长度必须在6-32位之间")

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 检查用户名是否已存在
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return RegisterResponse(success=False, message="用户名已被注册")

        # 密码加密
        password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(rounds=10)
        ).decode('utf-8')

        # 创建用户
        cursor.execute(
            """INSERT INTO users (username, password_hash, created_at, updated_at)
               VALUES (%s, %s, NOW(), NOW())""",
            (username, password_hash)
        )
        conn.commit()

        user_id = cursor.lastrowid
        token = create_token(user_id, username)

        return RegisterResponse(
            success=True,
            message="注册成功",
            token=token,
            user_id=user_id
        )

    except Error as e:
        if conn:
            conn.rollback()
        return RegisterResponse(success=False, message=f"数据库错误: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# EdgeOne Pages Cloud Functions 入口 - Handler 模式
class handler:
    def do_POST(self):
        import json
        from io import BytesIO

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body.decode('utf-8'))
            username = data.get('username', '').lower()
            password = data.get('password', '')

            # 验证输入
            if not username or not username.isalnum():
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "用户名只能包含字母和数字"}).encode())
                return

            if len(password) < 6 or len(password) > 32:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "密码长度必须在6-32位之间"}).encode())
                return

            conn = None
            cursor = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)

                # 检查用户名是否已存在
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "message": "用户名已被注册"}).encode())
                    return

                # 密码加密
                password_hash = bcrypt.hashpw(
                    password.encode('utf-8'),
                    bcrypt.gensalt(rounds=10)
                ).decode('utf-8')

                # 创建用户
                cursor.execute(
                    """INSERT INTO users (username, password_hash, created_at, updated_at)
                       VALUES (%s, %s, NOW(), NOW())""",
                    (username, password_hash)
                )
                conn.commit()

                user_id = cursor.lastrowid
                token = create_token(user_id, username)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "message": "注册成功",
                    "token": token,
                    "user_id": user_id
                }).encode())

            except Error as e:
                if conn:
                    conn.rollback()
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
