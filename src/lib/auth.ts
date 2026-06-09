import jwt from 'jsonwebtoken'

const JWT_SECRET = process.env.JWT_SECRET || 'sfm-cloud-jwt-secret-2024-secure-key'
const JWT_EXPIRE_DAYS = Number(process.env.JWT_EXPIRE_DAYS) || 7

export interface TokenPayload {
  user_id: number
  username: string
}

export function generateToken(payload: TokenPayload): string {
  return jwt.sign(payload, JWT_SECRET, {
    algorithm: 'HS256',
    expiresIn: `${JWT_EXPIRE_DAYS}d`,
  })
}

export function verifyToken(token: string): TokenPayload | null {
  try {
    return jwt.verify(token, JWT_SECRET, { algorithms: ['HS256'] }) as TokenPayload
  } catch {
    return null
  }
}

export function extractToken(authHeader: string | null): string | null {
  if (!authHeader || !authHeader.startsWith('Bearer ')) return null
  return authHeader.split(' ')[1]
}