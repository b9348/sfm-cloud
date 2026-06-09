import { NextResponse } from 'next/server'
import { getDB } from '@/lib/db'

export async function GET() {
  try {
    const conn = await getDB()
    const [rows] = await conn.query(
      'SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = ?',
      [process.env.DB_NAME || 'sfmmm1']
    )
    conn.release()

    const tables = (rows as { TABLE_NAME: string }[]).map(r => r.TABLE_NAME)

    return NextResponse.json({
      success: true,
      message: 'Database connection successful',
      tables,
    })
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : String(e)
    return NextResponse.json(
      { success: false, message: `Database error: ${message}` },
      { status: 500 }
    )
  }
}