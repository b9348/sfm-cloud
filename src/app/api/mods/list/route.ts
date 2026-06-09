import { NextRequest, NextResponse } from 'next/server'
import { getDB } from '@/lib/db'

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = req.nextUrl
    const lang = searchParams.get('lang') || 'en'
    const category = searchParams.get('category')
    const search = searchParams.get('search')
    const page = Math.max(1, Number(searchParams.get('page')) || 1)
    let limit = Number(searchParams.get('limit')) || 20
    if (limit > 100) limit = 100
    const offset = (page - 1) * limit

    const conn = await getDB()

    // 构建查询条件
    const whereConditions = ['m.is_public = TRUE']
    const queryParams: unknown[] = []

    if (category) {
      whereConditions.push('m.category = ?')
      queryParams.push(category)
    }

    if (search) {
      whereConditions.push(`(m.mod_id LIKE ?
        OR m.id IN (
          SELECT mod_id FROM mod_translations
          WHERE name LIKE ? OR description LIKE ?
        ))`)
      const searchPattern = `%${search}%`
      queryParams.push(searchPattern, searchPattern, searchPattern)
    }

    const whereClause = whereConditions.join(' AND ')

    // 查询总数
    const countSql = `SELECT COUNT(DISTINCT m.id) as total FROM mods m WHERE ${whereClause}`
    const [countResult] = await conn.query(countSql, queryParams)
    const total = (countResult as { total: number }[])[0].total

    // 查询 Mod 列表
    const sql = `
      SELECT
        m.id,
        m.mod_id as mod_key,
        m.version,
        m.category,
        m.download_count,
        m.created_at,
        m.updated_at,
        u.username as author_name,
        COALESCE(mt_target.name, mt_en.name, m.mod_id) as display_name,
        COALESCE(mt_target.description, mt_en.description, '') as description,
        CASE
          WHEN mt_target.name IS NOT NULL THEN ?
          WHEN mt_en.name IS NOT NULL THEN 'en'
          ELSE 'default'
        END as language
      FROM mods m
      JOIN users u ON m.author_id = u.id
      LEFT JOIN mod_translations mt_target ON m.id = mt_target.mod_id AND mt_target.lang_code = ?
      LEFT JOIN mod_translations mt_en ON m.id = mt_en.mod_id AND mt_en.lang_code = 'en'
      WHERE ${whereClause}
      ORDER BY m.created_at DESC
      LIMIT ? OFFSET ?
    `
    const [mods] = await conn.query(sql, [lang, lang, ...queryParams, limit, offset])

    const resultMods = (mods as Record<string, unknown>[]).map(mod => ({
      id: mod.id,
      mod_key: mod.mod_key,
      display_name: mod.display_name,
      description: mod.description || '',
      version: mod.version,
      category: mod.category,
      author: mod.author_name,
      download_count: mod.download_count,
      language: mod.language,
      created_at: mod.created_at instanceof Date ? mod.created_at.toISOString() : mod.created_at,
      updated_at: mod.updated_at instanceof Date ? mod.updated_at.toISOString() : mod.updated_at,
    }))

    conn.release()

    return NextResponse.json({
      success: true,
      data: {
        mods: resultMods,
        pagination: {
          page,
          limit,
          total,
          total_pages: total > 0 ? Math.ceil(total / limit) : 0,
        },
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