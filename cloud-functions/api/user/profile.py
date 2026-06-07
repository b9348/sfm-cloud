from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import mysql.connector
from mysql.connector import Error
import jwt

app = FastAPI()

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', '3306')),
    'database': os.environ.get('DB_NAME', 'sfm_cloud'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', '')
}

JWT_SECRET = os.environ.get('JWT_SECRET', 'default-secret-key')


class UserProfile(BaseModel):
    id: int
    username: str
    created_at: str
    last_login: Optional[str] = None


class UserModItem(BaseModel):
    mod_id: str
    name: str
    category: Optional[str] = None
    download_count: int
    is_public: bool
    is_approved: bool
    created_at: str


class UserProfileResponse(BaseModel):
    success: bool
    user: Optional[UserProfile] = None
    mods: List[UserModItem] = []


def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise HTTPException(status_code=500, detail=f"数据库连接失败: {str(e)}")


def verify_token(token: str) -> dict:
    try:
        if token.startswith('Bearer '):
            token = token[7:]
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的 Token")


@app.get("/api/user/profile")
async def get_profile(authorization: str = Header(None)):
    """获取当前用户信息（需要登录）"""
    if not authorization:
        raise HTTPException(status_code=401, detail="缺少认证信息")

    user = verify_token(authorization)
    user_id = user.get('user_id')

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 获取用户信息
        cursor.execute(
            """SELECT id, username, created_at, last_login
               FROM users WHERE id = %s""",
            (user_id,)
        )
        user_data = cursor.fetchone()

        if not user_data:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 获取用户创建的 Mod 列表
        cursor.execute(
            """SELECT m.mod_id, mt.name, m.category, m.download_count,
                      m.is_public, m.is_approved, m.created_at
               FROM mods m
               LEFT JOIN mod_translations mt ON m.id = mt.mod_id AND mt.lang_code = 'en'
               WHERE m.author_id = %s
               ORDER BY m.created_at DESC""",
            (user_id,)
        )
        mods = cursor.fetchall()

        user_profile = UserProfile(
            id=user_data['id'],
            username=user_data['username'],
            created_at=user_data['created_at'].isoformat() if user_data['created_at'] else None,
            last_login=user_data['last_login'].isoformat() if user_data['last_login'] else None
        )

        user_mods = [
            UserModItem(
                mod_id=m['mod_id'],
                name=m['name'] or m['mod_id'],
                category=m['category'],
                download_count=m['download_count'],
                is_public=m['is_public'],
                is_approved=m['is_approved'],
                created_at=m['created_at'].isoformat() if m['created_at'] else None
            )
            for m in mods
        ]

        return UserProfileResponse(
            success=True,
            user=user_profile,
            mods=user_mods
        )

    except Error as e:
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# EdgeOne Pages Cloud Functions 入口
class handler:
    def __init__(self):
        from mangum import Mangum
        self.asgi_handler = Mangum(app)

    async def __call__(self, scope, receive, send):
        await self.asgi_handler(scope, receive, send)
