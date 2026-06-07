from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import os
import mysql.connector
from mysql.connector import Error
import json

app = FastAPI()

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', '3306')),
    'database': os.environ.get('DB_NAME', 'sfm_cloud'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', '')
}

SUPPORTED_LANGUAGES = os.environ.get('SUPPORTED_LANGUAGES', 'zh,en,ja,ko,ru,fr,de').split(',')
DEFAULT_LANGUAGE = os.environ.get('DEFAULT_LANGUAGE', 'en')

LANGUAGE_NAMES = {
    'zh': '中文',
    'en': 'English',
    'ja': '日本語',
    'ko': '한국어',
    'ru': 'Русский',
    'fr': 'Français',
    'de': 'Deutsch'
}


class ModTranslationDetail(BaseModel):
    lang_code: str
    lang_name: str
    name: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    changelog: Optional[str] = None


class ModImage(BaseModel):
    image_url: str
    is_cover: bool
    sort_order: int


class ModDependency(BaseModel):
    mod_id: str
    name: str
    is_required: bool


class ModDetailResponse(BaseModel):
    success: bool
    data: dict


def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise HTTPException(status_code=500, detail=f"数据库连接失败: {str(e)}")


@app.get("/api/mods/detail/{mod_id}")
async def get_mod_detail(
    mod_id: str,
    lang: str = Query(DEFAULT_LANGUAGE)
):
    """获取Mod详情，包含所有语言版本"""
    conn = None
    cursor = None

    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 获取Mod基本信息
        cursor.execute("""
            SELECT m.id, m.mod_id, u.username as author_name, m.category,
                   m.tags, m.download_count, m.rating, m.rating_count,
                   m.file_size, m.file_url, m.file_hash, m.version,
                   m.is_public, m.is_approved, m.created_at, m.updated_at
            FROM mods m
            JOIN users u ON m.author_id = u.id
            WHERE m.mod_id = %s AND m.is_public = TRUE AND m.is_approved = TRUE
        """, (mod_id,))

        mod = cursor.fetchone()
        if not mod:
            raise HTTPException(status_code=404, detail="Mod 不存在或未通过审核")

        # 获取所有语言翻译
        cursor.execute("""
            SELECT lang_code, name, description, instructions, changelog
            FROM mod_translations
            WHERE mod_id = %s
        """, (mod['id'],))

        translations_raw = cursor.fetchall()
        translations: Dict[str, ModTranslationDetail] = {}

        for t in translations_raw:
            translations[t['lang_code']] = ModTranslationDetail(
                lang_code=t['lang_code'],
                lang_name=LANGUAGE_NAMES.get(t['lang_code'], t['lang_code']),
                name=t['name'],
                description=t['description'],
                instructions=t['instructions'],
                changelog=t['changelog']
            )

        # 确定当前显示的语言内容
        current_translation = translations.get(lang)
        if not current_translation:
            # 按优先级找可用语言
            for fallback_lang in ['en', 'zh'] + SUPPORTED_LANGUAGES:
                if fallback_lang in translations:
                    current_translation = translations[fallback_lang]
                    break

        # 获取图片
        cursor.execute("""
            SELECT image_url, is_cover, sort_order
            FROM mod_images
            WHERE mod_id = %s
            ORDER BY is_cover DESC, sort_order ASC
        """, (mod['id'],))

        images = [ModImage(**img) for img in cursor.fetchall()]

        # 获取依赖
        cursor.execute("""
            SELECT m.mod_id, mt.name, md.is_required
            FROM mod_dependencies md
            JOIN mods m ON md.dependency_mod_id = m.id
            LEFT JOIN mod_translations mt ON m.id = mt.mod_id AND mt.lang_code = %s
            WHERE md.mod_id = %s
        """, (lang, mod['id']))

        dependencies = []
        for dep in cursor.fetchall():
            dependencies.append(ModDependency(
                mod_id=dep['mod_id'],
                name=dep['name'] or dep['mod_id'],
                is_required=dep['is_required']
            ))

        # 解析tags
        tags = []
        if mod['tags']:
            try:
                tags = json.loads(mod['tags'])
            except:
                tags = []

        result = {
            'id': mod['id'],
            'mod_id': mod['mod_id'],
            'author_name': mod['author_name'],
            'category': mod['category'],
            'tags': tags,
            'download_count': mod['download_count'],
            'rating': float(mod['rating']),
            'rating_count': mod['rating_count'],
            'file_size': mod['file_size'],
            'file_hash': mod['file_hash'],
            'version': mod['version'],
            'created_at': mod['created_at'].isoformat() if mod['created_at'] else None,
            'updated_at': mod['updated_at'].isoformat() if mod['updated_at'] else None,
            # 当前语言内容
            'current_lang': lang,
            'name': current_translation.name if current_translation else mod['mod_id'],
            'description': current_translation.description if current_translation else None,
            'instructions': current_translation.instructions if current_translation else None,
            'changelog': current_translation.changelog if current_translation else None,
            # 所有可用语言
            'translations': {k: v.dict() for k, v in translations.items()},
            'available_languages': list(translations.keys()),
            # 图片和依赖
            'images': [img.dict() for img in images],
            'dependencies': [dep.dict() for dep in dependencies]
        }

        return ModDetailResponse(success=True, data=result)

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
