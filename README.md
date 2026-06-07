# SFM Cloud - EdgeOne Pages 云端后端

SFM Mod Manager 的云端功能后端，基于腾讯云 EdgeOne Pages Cloud Functions (Python/FastAPI) 构建。

## 功能特性

- **用户系统**: 登录、注册、JWT 认证
- **多语言 Mod 支持**: 支持 中英日韩俄法德 七种语言
- **Mod 管理**: 创建、查询、搜索 Mod
- **文件存储**: 支持 Mod 文件上传（需配合对象存储）

## 技术栈

- Python 3.10
- FastAPI
- MySQL
- JWT 认证

## 目录结构

```
sfm-cloud/
├── cloud-functions/          # EdgeOne Cloud Functions
│   ├── api/
│   │   ├── auth/            # 认证相关
│   │   │   ├── login.py     # 登录
│   │   │   └── register.py  # 注册
│   │   ├── mods/            # Mod 相关
│   │   │   ├── list.py      # Mod 列表
│   │   │   ├── detail.py    # Mod 详情
│   │   │   └── create.py    # 创建 Mod
│   │   └── user/            # 用户相关
│   │       └── profile.py   # 用户资料
│   └── requirements.txt     # Python 依赖
├── database/
│   └── schema.sql           # 数据库结构
├── .env.local               # 环境变量（已加入 gitignore）
├── edgeone.json             # EdgeOne 配置
└── README.md
```

## API 端点

### 认证
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录

### Mod
- `GET /api/mods/list` - 获取 Mod 列表（支持分页、搜索、多语言）
- `GET /api/mods/detail/{mod_id}` - 获取 Mod 详情
- `POST /api/mods/create` - 创建 Mod（需登录）

### 用户
- `GET /api/user/profile` - 获取用户信息（需登录）

## 多语言说明

Mod 名称和描述支持多语言存储，API 会根据请求参数 `lang` 返回对应语言的内容。

支持的语言代码：
- `zh` - 中文
- `en` - English
- `ja` - 日本語
- `ko` - 한국어
- `ru` - Русский
- `fr` - Français
- `de` - Deutsch

### 语言回退逻辑

1. 优先返回请求指定的语言
2. 如果没有该语言版本，按优先级 `en` > `zh` > 其他语言 查找
3. 返回第一个可用的语言版本

## 部署

### 1. 配置环境变量

复制 `.env.local` 中的内容到 EdgeOne Pages 控制台的环境变量设置中，并填写实际值：

```
DB_HOST=your-db-host.tencentcloud.com
DB_PORT=3306
DB_NAME=sfm_cloud
DB_USER=your_db_user
DB_PASSWORD=your_db_password
JWT_SECRET=your-random-secret-key
```

### 2. 部署到 EdgeOne Pages

```bash
# 安装 EdgeOne CLI
npm install -g edgeone

# 登录
edgeone login

# 部署
edgeone pages deploy
```

或使用 Git 集成自动部署：
1. 将代码推送到 Git 仓库
2. 在 EdgeOne Pages 控制台连接仓库
3. 自动构建部署

## 数据库设置

1. 创建 MySQL 数据库
2. 执行 `database/schema.sql` 创建表结构
3. 确保数据库允许 EdgeOne Pages 的 IP 访问

## 免费额度

EdgeOne Pages 免费套餐：
- Cloud Functions 请求数：100万次/月
- Cloud Functions GBs：50万/月
- KV 存储：1GB

## 注意事项

- `.env.local` 包含敏感信息，已加入 `.gitignore`，请勿提交到 Git
- 生产环境请使用强密码和随机 JWT_SECRET
- 建议启用数据库 SSL 连接
