import { NextRequest, NextResponse } from 'next/server'
import { getDB } from '@/lib/db'
import { verifyToken, extractToken } from '@/lib/auth'

export async function GET(req: NextRequest) {
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
    const conn = await getDB()

    // 查询用户信息
    const [userRows] = await conn.query(
      'SELECT id, username, created_at FROM users WHERE id = ?',
      [userId]
    )
    const users = userRows as { id: number; username: string; created_at: Date }[]

    if (users.length === 0) {
      conn.release()
      return NextResponse.json(
        { success: false, message: 'User not found' },
        { status: 404 }
      )
    }

    const user = users[0]

    // 查询用户的 Mod 数量
    const [countResult] = await conn.query(
      'SELECT COUNT(*) as count FROM mods WHERE author_id = ?',
      [userId]
    )
    const modCount = (countResult as { count: number }[])[0].count

    // 查询用户所有 Mods 的总下载量
    const [downloadResult] = await conn.query(
      'SELECT SUM(download_count) as total_downloads FROM mods WHERE author_id = ?',
      [userId]
    )
    const totalDownloads = (downloadResult as { total_downloads: number | null }[])[0].total_downloads || 0

    conn.release()

    return NextResponse.json({
      success: true,
      data: {
        user_id: user.id,
        username: user.username,
        created_at: user.created_at instanceof Date ? user.created_at.toISOString() : user.created_at,
        stats: {
          mod_count: modCount,
          total_downloads: totalDownloads,
        },
      },
    })
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : String(e)
    return NextResponse.json({ success: false, message }, { status: 500 })
  }
}