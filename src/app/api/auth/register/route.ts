import { NextRequest, NextResponse } from 'next/server'
import { getDB } from '@/lib/db'
import { generateToken } from '@/lib/auth'
import { createHash } from 'crypto'

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const username = (body.username || '').trim()
    const password = body.password || ''

    // 验证用户名
    if (!username) {
      return NextResponse.json({ success: false, message: 'Username is required' }, { status: 400 })
    }
    if (username.length < 1 || username.length > 32) {
      return NextResponse.json(
        { success: false, message: 'Username must be between 1 and 32 characters' },
        { status: 400 }
      )
    }
    if (!/^[a-zA-Z0-9]+$/.test(username)) {
      return NextResponse.json(
        { success: false, message: 'Username can only contain letters and numbers' },
        { status: 400 }
      )
    }

    // 验证密码
    if (!password) {
      return NextResponse.json({ success: false, message: 'Password is required' }, { status: 400 })
    }
    if (password.length < 6 || password.length > 32) {
      return NextResponse.json(
        { success: false, message: 'Password must be between 6 and 32 characters' },
        { status: 400 }
      )
    }

    const conn = await getDB()

    // 检查用户名是否已存在
    const [existing] = await conn.query('SELECT id FROM users WHERE username = ?', [username])
    if ((existing as unknown[]).length > 0) {
      conn.release()
      return NextResponse.json(
        { success: false, message: 'Username already exists' },
        { status: 409 }
      )
    }

    // 密码加密
    const passwordHash = createHash('sha256').update(password).digest('hex')

    // 创建用户
    const [result] = await conn.execute(
      'INSERT INTO users (username, password_hash) VALUES (?, ?)',
      [username, passwordHash]
    )
    const userId = (result as { insertId: number }).insertId

    // 生成 JWT Token
    const token = generateToken({ user_id: userId, username })

    conn.release()

    return NextResponse.json(
      {
        success: true,
        message: 'User registered successfully',
        data: { user_id: userId, username, token },
      },
      { status: 201 }
    )
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : String(e)
    return NextResponse.json({ success: false, message }, { status: 500 })
  }
}