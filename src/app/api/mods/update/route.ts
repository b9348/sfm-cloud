import { NextRequest, NextResponse } from 'next/server'
import { getDB } from '@/lib/db'
import { verifyToken, extractToken } from '@/lib/auth'

const SUPPORTED_LANGUAGES = ['zh', 'en', 'ja', 'ko', 'ru', 'fr', 'de']

export async function PUT(req: NextRequest) {
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
    const modId = body.mod_id

    if (!modId) {
      return NextResponse.json(
        { success: false, message: 'Mod ID is required' },
        { status: 400 }
      )
    }

    const conn = await getDB()

    // 检查 Mod 是否存在且属于当前用户
    const [modRows] = await conn.query(
      'SELECT id, author_id FROM mods WHERE id = ?',
      [modId]
    )
    const mods = modRows as { id: number; author_id: number }[]

    if (mods.length === 0) {
      conn.release()
      return NextResponse.json(
        { success: false, message: 'Mod not found' },
        { status: 404 }
      )
    }

    if (mods[0].author_id !== userId) {
      conn.release()
      return NextResponse.json(
        { success: false, message: 'You can only update your own mods' },
        { status: 403 }
      )
    }

    // 更新 Mod 基本信息
    const updates: string[] = []
    const params: (string | number | boolean)[] = []

    if ('version' in body) {
      updates.push('version = ?')
      params.push(body.version)
    }
    if ('category' in body) {
      updates.push('category = ?')
      params.push(body.category)
    }
    if ('is_public' in body) {
      updates.push('is_public = ?')
      params.push(body.is_public)
    }

    if (updates.length > 0) {
      params.push(modId)
      await conn.execute(
        `UPDATE mods SET ${updates.join(', ')} WHERE id = ?`,
        params
      )
    }

    // 更新多语言内容
    if ('translations' in body) {
      for (const [langCode, content] of Object.entries(body.translations) as [string, Record<string, string>][]) {
        if (!SUPPORTED_LANGUAGES.includes(langCode)) continue

        const name = (content.name || '').trim()
        const description = (content.description || '').trim()
        const instructions = (content.instructions || '').trim()
        const changelog = (content.changelog || '').trim()

        // 检查是否已存在该语言的翻译
        const [existing] = await conn.query(
          'SELECT id FROM mod_translations WHERE mod_id = ? AND lang_code = ?',
          [modId, langCode]
        )

        if ((existing as unknown[]).length > 0) {
          if (name) {
            await conn.execute(
              'UPDATE mod_translations SET name = ?, description = ?, instructions = ?, changelog = ? WHERE mod_id = ? AND lang_code = ?',
              [name, description, instructions, changelog, modId, langCode]
            )
          }
        } else {
          if (name) {
            await conn.execute(
              'INSERT INTO mod_translations (mod_id, lang_code, name, description, instructions, changelog) VALUES (?, ?, ?, ?, ?, ?)',
              [modId, langCode, name, description, instructions, changelog]
            )
          }
        }
      }
    }

    conn.release()

    return NextResponse.json({
      success: true,
      message: 'Mod updated successfully',
      data: { mod_id: modId },
    })
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : String(e)
    return NextResponse.json(
      { success: false, message: `Server error: ${message}` },
      { status: 500 }
    )
  }
}