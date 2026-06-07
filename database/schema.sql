-- SFM Cloud 数据库结构
-- 支持多语言的 Mod 云端存储系统

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(32) NOT NULL UNIQUE COMMENT '用户名，字母数字',
    password_hash VARCHAR(255) NOT NULL COMMENT 'bcrypt加密后的密码',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login DATETIME NULL,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- Mod 主表
CREATE TABLE IF NOT EXISTS mods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mod_id VARCHAR(64) NOT NULL UNIQUE COMMENT 'Mod唯一标识符',
    author_id INT NOT NULL COMMENT '作者用户ID',
    category VARCHAR(50) NULL COMMENT '分类',
    tags JSON NULL COMMENT '标签数组',
    download_count INT DEFAULT 0 COMMENT '下载次数',
    rating DECIMAL(2,1) DEFAULT 5.0 COMMENT '评分 0-5',
    rating_count INT DEFAULT 0 COMMENT '评分人数',
    file_size BIGINT NULL COMMENT '文件大小(字节)',
    file_url VARCHAR(500) NULL COMMENT '文件存储URL',
    file_hash VARCHAR(64) NULL COMMENT '文件SHA256哈希',
    version VARCHAR(32) DEFAULT '1.0.0' COMMENT '版本号',
    is_public BOOLEAN DEFAULT TRUE COMMENT '是否公开',
    is_approved BOOLEAN DEFAULT FALSE COMMENT '是否审核通过',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_author (author_id),
    INDEX idx_category (category),
    INDEX idx_public (is_public, is_approved),
    INDEX idx_download_count (download_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Mod主表';

-- Mod 多语言内容表
CREATE TABLE IF NOT EXISTS mod_translations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mod_id INT NOT NULL COMMENT '关联mods.id',
    lang_code VARCHAR(10) NOT NULL COMMENT '语言代码: zh,en,ja,ko,ru,fr,de',
    name VARCHAR(255) NOT NULL COMMENT 'Mod名称',
    description TEXT NULL COMMENT 'Mod描述',
    instructions TEXT NULL COMMENT '使用说明',
    changelog TEXT NULL COMMENT '更新日志',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE,
    UNIQUE KEY uk_mod_lang (mod_id, lang_code),
    INDEX idx_lang_code (lang_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Mod多语言内容表';

-- Mod 图片/截图表
CREATE TABLE IF NOT EXISTS mod_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mod_id INT NOT NULL COMMENT '关联mods.id',
    image_url VARCHAR(500) NOT NULL COMMENT '图片URL',
    sort_order INT DEFAULT 0 COMMENT '排序',
    is_cover BOOLEAN DEFAULT FALSE COMMENT '是否封面图',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE,
    INDEX idx_mod_id (mod_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Mod图片表';

-- Mod 依赖关系表
CREATE TABLE IF NOT EXISTS mod_dependencies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mod_id INT NOT NULL COMMENT '主Mod ID',
    dependency_mod_id INT NOT NULL COMMENT '依赖的Mod ID',
    is_required BOOLEAN DEFAULT TRUE COMMENT '是否必需',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE,
    FOREIGN KEY (dependency_mod_id) REFERENCES mods(id) ON DELETE CASCADE,
    UNIQUE KEY uk_mod_dep (mod_id, dependency_mod_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Mod依赖关系表';

-- 用户收藏表
CREATE TABLE IF NOT EXISTS user_favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    mod_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_mod (user_id, mod_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户收藏表';

-- 用户评分表
CREATE TABLE IF NOT EXISTS user_ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    mod_id INT NOT NULL,
    rating TINYINT NOT NULL COMMENT '评分 1-5',
    comment TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_mod_rating (user_id, mod_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户评分表';

-- 下载记录表
CREATE TABLE IF NOT EXISTS download_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mod_id INT NOT NULL,
    user_id INT NULL COMMENT '登录用户ID，未登录为NULL',
    ip_address VARCHAR(45) NULL COMMENT 'IP地址',
    user_agent VARCHAR(500) NULL,
    downloaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE,
    INDEX idx_mod_id (mod_id),
    INDEX idx_downloaded_at (downloaded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='下载记录表';

-- 语言配置表 (方便扩展)
CREATE TABLE IF NOT EXISTS languages (
    code VARCHAR(10) PRIMARY KEY COMMENT '语言代码',
    name_zh VARCHAR(50) NOT NULL COMMENT '中文名称',
    name_native VARCHAR(50) NOT NULL COMMENT '本地名称',
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='语言配置表';

-- 插入支持的语言
INSERT INTO languages (code, name_zh, name_native, sort_order) VALUES
('zh', '中文', '中文', 1),
('en', '英语', 'English', 2),
('ja', '日语', '日本語', 3),
('ko', '韩语', '한국어', 4),
('ru', '俄语', 'Русский', 5),
('fr', '法语', 'Français', 6),
('de', '德语', 'Deutsch', 7)
ON DUPLICATE KEY UPDATE name_zh=VALUES(name_zh), name_native=VALUES(name_native);
