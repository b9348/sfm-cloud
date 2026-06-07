from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import mysql.connector
from mysql.connector import Error

app = FastAPI()

# 从环境变量读取配置
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', '3306')),
    'database': os.environ.get('DB_NAME', 'sfm_cloud'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', '')
}

SUPPORTED_LANGUAGES = os.environ.get('SUPPORTED_LANGUAGES', 'zh,en,ja,ko,ru,fr,de').split(',')
DEFAULT_LANGUAGE = os.environ.get('DEFAULT_LANGUAGE', 'en')


class ModTranslation(BaseModel):
    lang_code: str
    name: str
    description: Optional[str] = None


class ModItem(BaseModel):
    id: int
    mod_id: str
    author_name: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    download_count: int
    rating: float
    file_size: Optional[int] = None
    version: str
    cover_image: Optional[str] = None
    # 当前语言的内容
    name: str
    description: Optional[str] = None
    # 所有可用语言
    available_languages: List[str]
    created_at: str


class ModListResponse(BaseModel):
    success: bool
    data: List[ModItem]
    total: int
    page: int
    page_size: int


def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise HTTPException(status_code=500, detail=f"数据库连接失败: {str(e)}")


def get_mod_translation(conn, mod_id: int, preferred_lang: str) -> dict:
    """获取Mod的翻译内容，优先返回指定语言，没有则返回第一个可用语言"""
    cursor = conn.cursor(dictionary=True)
    try:
        # 先尝试获取首选语言
        cursor.execute(
            """SELECT lang_code, name, description
               FROM mod_translations
               WHERE mod_id = %s AND lang_code = %s""",
            (mod_id, preferred_lang)
        )
        result = cursor.fetchone()

        if result:
            return result

        # 没有首选语言，获取第一个可用语言
        cursor.execute(
            """SELECT lang_code, name, description
               FROM mod_translations
               WHERE mod_id = %s
               ORDER BY FIELD(lang_code, 'en', 'zh', 'ja', 'ko', 'ru', 'fr', 'de')
               LIMIT 1""",
            (mod_id,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()


def get_available_languages(conn, mod_id: int) -> List[str]:
    """获取Mod支持的所有语言"""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT lang_code FROM mod_translations WHERE mod_id = %s",
            (mod_id,)
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        cursor.close()


@app.get("/api/mods/list")
async def list_mods(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    lang: str = Query(DEFAULT_LANGUAGE),
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("download_count", regex="^(download_count|rating|created_at|updated_at)$")
):
    """获取Mod列表，支持多语言"""
    conn = None
    cursor = None

    # 验证语言代码
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 构建查询条件
        where_conditions = ["m.is_public = TRUE", "m.is_approved = TRUE"]
        params = []

        if category:
            where_conditions.append("m.category = %s")
            params.append(category)

        if search:
            # 搜索支持多语言，需要在翻译表中查找
            where_conditions.append("""(
                EXISTS (
                    SELECT 1 FROM mod_translations mt
                    WHERE mt.mod_id = m.id
                    AND (mt.name LIKE %s OR mt.description LIKE %s)
                )
            )""")
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])

        where_clause = " AND ".join(where_conditions)

        # 获取总数
        count_sql = f"SELECT COUNT(*) as total FROM mods m WHERE {where_clause}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total']

        # 排序字段映射
        sort_mapping = {
            'download_count': 'm.download_count DESC',
            'rating': 'm.rating DESC',
            'created_at': 'm.created_at DESC',
            'updated_at': 'm.updated_at DESC'
        }
        order_by = sort_mapping.get(sort_by, 'm.download_count DESC')

        # 获取Mod列表
        offset = (page - 1) * page_size
        sql = f"""
            SELECT m.id, m.mod_id, u.username as author_name, m.category,
                   m.tags, m.download_count, m.rating, m.file_size,
                   m.version, m.created_at,
                   (SELECT image_url FROM mod_images WHERE mod_id = m.id AND is_cover = TRUE LIMIT 1) as cover_image
            FROM mods m
            JOIN users u ON m.author_id = u.id
            WHERE {where_clause}
            ORDER BY {order_by}
            LIMIT %s OFFSET %s
        """
        cursor.execute(sql, params + [page_size, offset])
        mods = cursor.fetchall()

        # 处理每个Mod的多语言内容
        result = []
        for mod in mods:
            # 获取翻译内容
            translation = get_mod_translation(conn, mod['id'], lang)
            available_langs = get_available_languages(conn, mod['id'])

            # 解析tags
            tags = None
            if mod['tags']:
                import json
                try:
                    tags = json.loads(mod['tags'])
                except:
                    tags = []

            result.append(ModItem(
                id=mod['id'],
                mod_id=mod['mod_id'],
                author_name=mod['author_name'],
                category=mod['category'],
                tags=tags,
                download_count=mod['download_count'],
                rating=float(mod['rating']),
                file_size=mod['file_size'],
                version=mod['version'],
                cover_image=mod['cover_image'],
                name=translation['name'] if translation else mod['mod_id'],
                description=translation['description'] if translation else None,
                available_languages=available_langs,
                created_at=mod['created_at'].isoformat() if mod['created_at'] else None
            ))

        return ModListResponse(
            success=True,
            data=result,
            total=total,
            page=page,
            page_size=page_size
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
