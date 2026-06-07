# SFM Cloud API

SFM Cloud 后端 API，基于腾讯云 EdgeOne Pages Python Cloud Functions 构建。

## 功能特性

- 用户注册/登录（JWT 认证）
- Mod 多语言支持（中英日韩俄法德）
- 云端 Mod 管理

## 技术栈

- Python 3.10
- EdgeOne Pages Cloud Functions
- MySQL 数据库
- JWT 认证

## API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |

## 部署

通过 Git 集成自动部署到 EdgeOne Pages。

## 环境变量

复制 `.env.example` 为 `.env.local` 并填写实际值：

```bash
cp .env.example .env.local
```
