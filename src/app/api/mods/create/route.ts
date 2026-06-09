import { NextRequest, NextResponse } from 'next/server'
import { getDB } from '@/lib/db'
import { verifyToken, extractToken } from '@/lib/auth'

const SUPPORTED_LANGUAGES = ['zh', 'en', 'ja', 'ko', 'ru', 'fr', 'de']

export async function POST(req: NextRequest) {
  try {
    // 验证 JWT Token
    const token = extractToken(req.headers.get('Authorization'))
    if (!token) {
      return NextResponse.json(
        { success: false, message: 'Missing or invalid authorization header' },
        { status: 401 }
      )
    }

    const payload = verifyToken(token)
    if (!payload) {
      return NextResponse.json(
        { success: false, message: 'Invalid or expired token' },
        { status: 401 }
      )
    }

    const userId = payload.user_id
    const body = await req.json()
    const modKey = (body.mod_key || '').trim()
    const translations = body.translations || {}
    const category = body.category || 'other'
    const version = body.version || '1.0.0'

    // 验证必填字段
    if (!modKey) {
      return NextResponse.json(
        { success: false, message: 'Mod key is required' },
        { status: 400 }
      )
    }

    if (!/^[a-zA-Z0-9_-]+$/.test(modKey)) {
      return NextResponse.json(
        { success: false, message: 'Mod key can only contain letters, numbers, underscores and hyphens' },
        { status: 400 }
      )
    }

    if (!translations || Object.keys(translations).length === 0) {
      return NextResponse.json(
        { success: false, message: 'At least one language translation is required' },
        { status: 400 }
      )
    }

    const conn = await getDB()

    // 检查 Mod key 是否已存在
    const [existing] = await conn.query('SELECT id FROM mods WHERE mod_id = ?', [modKey])
    if ((existing as unknown[]).length > 0) {
      conn.release()
      return NextResponse.json(
        { success: false, message: 'Mod key already exists' },
        { status: 409 }
      )
    }

    // 创建 Mod
    const [result] = await conn.execute(
      'INSERT INTO mods (author_id, mod_id, version, category, is_public) VALUES (?, ?, ?, ?, ?)',
      [userId, modKey, version, category, true]
    )
    const modId = (result as { insertId: number }).insertId

    // 创建多语言内容
    for (const [langCode, content] of Object.entries(translations) as [string, Record<string, string>][]) {
      if (!SUPPORTED_LANGUAGES.includes(langCode)) continue

      const name = (content.name || '').trim()
      const description = (content.description || '').trim()
      const instructions = (content.instructions || '').trim()
      const changelog = (content.changelog || '').trim()

      if (name) {
        await conn.execute(
          'INSERT INTO mod_translations (mod_id, lang_code, name, description, instructions, changelog) VALUES (?, ?, ?, ?, ?, ?)',
          [modId, langCode, name, description, instructions, changelog]
        )
      }
    }

    conn.release()

    return NextResponse.json(
      {
        success: true,
        message: 'Mod created successfully',
        data: {
          mod_id: modId,
          mod_key: modKey,
          version,
          category,
          translations: Object.keys(translations),
        },
      },
      { status: 201 }
    )
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : String(e)
    return NextResponse.json(
      { success: false, message: `Server error: ${message}` },
      { status: 500 }
    )
  }
}