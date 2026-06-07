from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import os
import mysql.connector
from mysql.connector import Error
import jwt
import json
import re
import uuid

app = FastAPI()

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', '3306')),
    'database': os.environ.get('DB_NAME', 'sfm_cloud'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', '')
}

JWT_SECRET = os.environ.get('JWT_SECRET', 'default-secret-key')
SUPPORTED_LANGUAGES = os.environ.get('SUPPORTED_LANGUAGES', 'zh,en,ja,ko,ru,fr,de').split(',')


class ModTranslationInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    instructions: Optional[str] = Field(None, max_length=10000)
    changelog: Optional[str] = Field(None, max_length=5000)


class ModCreateRequest(BaseModel):
    # 多语言内容，key 是语言代码
    translations: Dict[str, ModTranslationInput]
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None
    version: str = Field(default="1.0.0", max_length=32)
    is_public: bool = True
    dependencies: Optional[List[str]] = None  # 依赖的 mod_id 列表


class ModCreateResponse(BaseModel):
    success: bool
    message: str
    mod_id: Optional[str] = None


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


def generate_mod_id() -> str:
    """生成唯一的 mod_id"""
    return f"mod_{uuid.uuid4().hex[:12]}"


def validate_translations(translations: Dict[str, ModTranslationInput]) -> bool:
    """验证翻译内容"""
    if not translations:
        return False

    # 至少需要一个语言版本
    for lang_code, content in translations.items():
        if lang_code not in SUPPORTED_LANGUAGES:
            return False
        if not content.name or len(content.name.strip()) == 0:
            return False
    return True


@app.post("/api/mods/create")
async def create_mod(
    data: ModCreateRequest,
    authorization: str = Header(None)
):
    """创建新的 Mod（需要登录）"""
    if not authorization:
        raise HTTPException(status_code=401, detail="缺少认证信息")

    # 验证用户
    user = verify_token(authorization)
    user_id = user.get('user_id')

    # 验证翻译内容
    if not validate_translations(data.translations):
        return ModCreateResponse(
            success=False,
            message="翻译内容无效，请确保至少提供一种语言的名称"
        )

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 生成 mod_id
        mod_id = generate_mod_id()

        # 插入 mods 表
        cursor.execute(
            """INSERT INTO mods (mod_id, author_id, category, tags, version, is_public, is_approved)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                mod_id,
                user_id,
                data.category,
                json.dumps(data.tags) if data.tags else None,
                data.version,
                data.is_public,
                False  # 新创建的 mod 需要审核
            )
        )

        mod_db_id = cursor.lastrowid

        # 插入翻译内容
        for lang_code, translation in data.translations.items():
            cursor.execute(
                """INSERT INTO mod_translations
                   (mod_id, lang_code, name, description, instructions, changelog)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    mod_db_id,
                    lang_code,
                    translation.name,
                    translation.description,
                    translation.instructions,
                    translation.changelog
                )
            )

        # 处理依赖关系
        if data.dependencies:
            for dep_mod_id in data.dependencies:
                # 查找依赖的 mod
                cursor.execute("SELECT id FROM mods WHERE mod_id = %s", (dep_mod_id,))
                dep = cursor.fetchone()
                if dep:
                    cursor.execute(
                        """INSERT INTO mod_dependencies (mod_id, dependency_mod_id, is_required)
                           VALUES (%s, %s, %s)""",
                        (mod_db_id, dep['id'], True)
                    )

        conn.commit()

        return ModCreateResponse(
            success=True,
            message="Mod 创建成功，等待审核",
            mod_id=mod_id
        )

    except Error as e:
        if conn:
            conn.rollback()
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
