import { NextRequest, NextResponse } from 'next/server'
import { getDB } from '@/lib/db'
import { verifyToken, extractToken } from '@/lib/auth'

export async function DELETE(req: NextRequest) {
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
      'SELECT id, author_id, mod_id FROM mods WHERE id = ?',
      [modId]
    )
    const mods = modRows as { id: number; author_id: number; mod_id: string }[]

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
        { success: false, message: 'You can only delete your own mods' },
        { status: 403 }
      )
    }

    const modKey = mods[0].mod_id

    // 删除 Mod（级联删除会自动删除关联的翻译、图片等）
    await conn.execute('DELETE FROM mods WHERE id = ?', [modId])

    conn.release()

    return NextResponse.json({
      success: true,
      message: 'Mod deleted successfully',
      data: { mod_id: modId, mod_key: modKey },
    })
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : String(e)
    return NextResponse.json(
      { success: false, message: `Server error: ${message}` },
      { status: 500 }
    )
  }
}