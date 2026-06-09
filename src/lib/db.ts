import mysql from 'mysql2/promise'

const pool = mysql.createPool({
  host: process.env.DB_HOST || 'mysql7.sqlpub.com',
  port: Number(process.env.DB_PORT) || 3312,
  user: process.env.DB_USER || 'sfmmm1',
  password: process.env.DB_PASSWORD || 'fEPM4xyhL3WAVGYf',
  database: process.env.DB_NAME || 'sfmmm1',
  charset: 'utf8mb4',
  waitForConnections: true,
  connectionLimit: 10,
  connectTimeout: 10000,
})

export function getDB() {
  return pool.getConnection()
}

export default pool