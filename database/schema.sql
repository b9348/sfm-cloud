-- SFM Cloud 数据库结构

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(32) NOT NULL UNIQUE COMMENT '用户名（字母+数字）',
    password_hash VARCHAR(64) NOT NULL COMMENT 'SHA256加密后的密码',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- Mod 主表
CREATE TABLE IF NOT EXISTS mods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    author_id INT NOT NULL COMMENT '作者ID',
    name VARCHAR(100) NOT NULL COMMENT 'Mod唯一标识名（英文）',
    version VARCHAR(20) DEFAULT '1.0.0' COMMENT '版本号',
    category ENUM('animation', 'model', 'texture', 'sound', 'script', 'other') DEFAULT 'other' COMMENT '分类',
    download_count INT DEFAULT 0 COMMENT '下载次数',
    is_public BOOLEAN DEFAULT TRUE COMMENT '是否公开',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_name (name),
    INDEX idx_author (author_id),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Mod主表';

-- Mod 多语言内容表
CREATE TABLE IF NOT EXISTS mod_translations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mod_id INT NOT NULL COMMENT 'Mod ID',
    language VARCHAR(10) NOT NULL COMMENT '语言代码: zh, en, ja, ko, ru, fr, de',
    display_name VARCHAR(200) NOT NULL COMMENT '显示名称',
    description TEXT COMMENT 'Mod描述',
    instructions TEXT COMMENT '使用说明',
    changelog TEXT COMMENT '更新日志',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE,
    UNIQUE KEY uk_mod_lang (mod_id, language),
    INDEX idx_language (language)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Mod多语言内容表';

-- Mod 图片表
CREATE TABLE IF NOT EXISTS mod_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mod_id INT NOT NULL COMMENT 'Mod ID',
    image_url VARCHAR(500) NOT NULL COMMENT '图片URL',
    sort_order INT DEFAULT 0 COMMENT '排序顺序',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE,
    INDEX idx_mod_sort (mod_id, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Mod图片表';

-- Mod 依赖关系表
CREATE TABLE IF NOT EXISTS mod_dependencies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mod_id INT NOT NULL COMMENT 'Mod ID',
    dependency_mod_id INT NOT NULL COMMENT '依赖的Mod ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE,
    FOREIGN KEY (dependency_mod_id) REFERENCES mods(id) ON DELETE CASCADE,
    UNIQUE KEY uk_mod_dep (mod_id, dependency_mod_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Mod依赖关系表';

-- Mod 文件表
CREATE TABLE IF NOT EXISTS mod_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mod_id INT NOT NULL COMMENT 'Mod ID',
    file_url VARCHAR(500) NOT NULL COMMENT '文件URL',
    file_name VARCHAR(200) NOT NULL COMMENT '文件名',
    file_size BIGINT DEFAULT 0 COMMENT '文件大小(字节)',
    version VARCHAR(20) DEFAULT '1.0.0' COMMENT '版本号',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mod_id) REFERENCES mods(id) ON DELETE CASCADE,
    INDEX idx_mod_version (mod_id, version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Mod文件表';
