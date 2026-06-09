/** @type {import('next').NextConfig} */
const nextConfig = {
  // EdgeOne Pages Serverless 环境需要 standalone 输出模式
  output: 'standalone',
  experimental: {
    // Next.js 14 中外部包配置在 experimental 下（15+ 才升级为顶层 serverExternalPackages）
    serverComponentsExternalPackages: ['mysql2', 'jsonwebtoken'],
  },
}

module.exports = nextConfig
