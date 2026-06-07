"""
共享工具函数
"""
import os
import re
import jwt
import pymysql
from datetime import datetime, timedelta

def create_db_connection():
    """创建数据库连接"""
    return pymysql.connect(
        host=os.environ.get('DB_HOST', 'mysql7.sqlpub.com'),
        port=int(os.environ.get('DB_PORT', '3312')),
        user=os.environ.get('DB_USER', 'sfmmm1'),
        password=os.environ.get('DB_PASSWORD', 'fEPM4xyhL3WAVGYf'),
        database=os.environ.get('DB_NAME', 'sfmmm1'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def validate_username(username):
    """验证用户名"""
    if not username:
        return False, "Username is required"
    if len(username) < 1:
        return False, "Username must be at least 1 character"
    if len(username) > 32:
        return False, "Username must be at most 32 characters"
    if not re.match(r'^[a-zA-Z0-9]+$', username):
        return False, "Username can only contain letters and numbers"
    return True, None

def validate_password(password):
    """验证密码"""
    if not password:
        return False, "Password is required"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if len(password) > 32:
        return False, "Password must be at most 32 characters"
    return True, None

def generate_jwt(user_id, username):
    """生成 JWT Token"""
    secret = os.environ.get('JWT_SECRET', 'sfm-cloud-jwt-secret-2024-secure-key')
    expire_days = int(os.environ.get('JWT_EXPIRE_DAYS', '7'))
    
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(days=expire_days),
        'iat': datetime.utcnow()
    }
    
    return jwt.encode(payload, secret, algorithm='HS256')

def verify_jwt(token):
    """验证 JWT Token"""
    try:
        secret = os.environ.get('JWT_SECRET', 'sfm-cloud-jwt-secret-2024-secure-key')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token has expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"
