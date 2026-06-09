import { NextRequest, NextResponse } from 'next/server'
import { getDB } from '@/lib/db'

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const modId = Number(params.id)
    if (!modId || isNaN(modId)) {
      return NextResponse.json(
        { success: false, message: 'Invalid mod ID' },
        { status: 400 }
      )
    }

    const lang = req.nextUrl.searchParams.get('lang') || 'en'

    const conn = await getDB()

    // 查询 Mod 详情
    const sql = `
      SELECT
        m.id,
        m.mod_id as mod_key,
        m.version,
        m.category,
        m.download_count,
        m.is_public,
        m.created_at,
        m.updated_at,
        u.username as author_name,
        COALESCE(mt_target.name, mt_en.name, m.mod_id) as display_name,
        COALESCE(mt_target.description, mt_en.description, '') as description,
        COALESCE(mt_target.instructions, mt_en.instructions, '') as instructions,
        COALESCE(mt_target.changelog, mt_en.changelog, '') as changelog,
        CASE
          WHEN mt_target.name IS NOT NULL THEN ?
          WHEN mt_en.name IS NOT NULL THEN 'en'
          ELSE 'default'
        END as language
      FROM mods m
      JOIN users u ON m.author_id = u.id
      LEFT JOIN mod_translations mt_target ON m.id = mt_target.mod_id AND mt_target.lang_code = ?
      LEFT JOIN mod_translations mt_en ON m.id = mt_en.mod_id AND mt_en.lang_code = 'en'
      WHERE m.id = ? AND m.is_public = TRUE
    `
    const [rows] = await conn.query(sql, [lang, lang, modId])
    const mods = rows as Record<string, unknown>[]

    if (mods.length === 0) {
      conn.release()
      return NextResponse.json(
        { success: false, message: 'Mod not found' },
        { status: 404 }
      )
    }

    const mod = mods[0]

    // 查询所有可用语言
    const [langRows] = await conn.query(
      'SELECT lang_code FROM mod_translations WHERE mod_id = ?',
      [modId]
    )
    const availableLanguages = (langRows as { lang_code: string }[]).map(r => r.lang_code)

    conn.release()

    return NextResponse.json({
      success: true,
      data: {
        id: mod.id,
        mod_key: mod.mod_key,
        display_name: mod.display_name,
        description: mod.description || '',
        instructions: mod.instructions || '',
        changelog: mod.changelog || '',
        version: mod.version,
        category: mod.category,
        author: mod.author_name,
        download_count: mod.download_count,
        language: mod.language,
        available_languages: availableLanguages,
        created_at: mod.created_at instanceof Date ? mod.created_at.toISOString() : mod.created_at,
        updated_at: mod.updated_at instanceof Date ? mod.updated_at.toISOString() : mod.updated_at,
      },
    })
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : String(e)
    return NextResponse.json(
      { success: false, message: `Server error: ${message}` },
      { status: 500 }
    )
  }
}