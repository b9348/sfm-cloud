import { NextRequest, NextResponse } from 'next/server'
import { getDB } from '@/lib/db'
import { generateToken } from '@/lib/auth'
import { createHash } from 'crypto'

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const username = (body.username || '').trim()
    const password = body.password || ''

    if (!username || !password) {
      return NextResponse.json(
        { success: false, message: 'Username and password are required' },
        { status: 400 }
      )
    }

    const conn = await getDB()

    // 查找用户
    const [rows] = await conn.query(
      'SELECT id, username, password_hash FROM users WHERE username = ?',
      [username]
    )
    const users = rows as { id: number; username: string; password_hash: string }[]

    if (users.length === 0) {
      conn.release()
      return NextResponse.json(
        { success: false, message: 'Invalid username or password' },
        { status: 401 }
      )
    }

    const user = users[0]

    // 验证密码
    const passwordHash = createHash('sha256').update(password).digest('hex')
    if (passwordHash !== user.password_hash) {
      conn.release()
      return NextResponse.json(
        { success: false, message: 'Invalid username or password' },
        { status: 401 }
      )
    }

    // 生成 JWT Token
    const token = generateToken({ user_id: user.id, username: user.username })

    conn.release()

    return NextResponse.json({
      success: true,
      message: 'Login successful',
      data: { user_id: user.id, username: user.username, token },
    })
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : String(e)
    return NextResponse.json({ success: false, message }, { status: 500 })
  }
}