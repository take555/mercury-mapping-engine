-- カテゴリマスタ
CREATE TABLE mercury_category2 (
    id INT UNSIGNED NOT NULL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    order_display INT DEFAULT 1,
    active TINYINT(4) NOT NULL DEFAULT 1,
    updated_at DATETIME DEFAULT NULL,
    created_at DATETIME DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 会社マスタ
CREATE TABLE mercury_company (
    id INT PRIMARY KEY AUTO_INCREMENT,
    company_code VARCHAR(10) NOT NULL,
    company_name VARCHAR(100) NOT NULL,
    active TINYINT(4) NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT NULL,
    updated_at DATETIME DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- マッピングルール
CREATE TABLE mercury_common_mapping_rule (
    id INT PRIMARY KEY AUTO_INCREMENT,
    category2_id INT UNSIGNED NOT NULL,
    company_a_id INT NOT NULL,
    company_b_id INT NOT NULL,
    company_a_field VARCHAR(100) NOT NULL,
    company_b_field VARCHAR(100) NOT NULL,
    common_field_name VARCHAR(50) NOT NULL,
    mapping_type ENUM('direct', 'transform', 'extract') DEFAULT 'direct',
    transform_rule JSON,
    priority INT DEFAULT 1,
    active TINYINT(4) NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT NULL,
    updated_at DATETIME DEFAULT NULL,
    FOREIGN KEY (category2_id) REFERENCES mercury_category2(id),
    FOREIGN KEY (company_a_id) REFERENCES mercury_company(id),
    FOREIGN KEY (company_b_id) REFERENCES mercury_company(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 正規化ルール  
CREATE TABLE mercury_normalization_rule (
    id INT PRIMARY KEY AUTO_INCREMENT,
    category2_id INT UNSIGNED NOT NULL,
    field_name VARCHAR(50) NOT NULL,
    rule_type ENUM('text_clean', 'split', 'value_map', 'regex') NOT NULL,
    rule_config JSON NOT NULL,
    execution_order INT DEFAULT 1,
    active TINYINT(4) NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT NULL,
    updated_at DATETIME DEFAULT NULL,
    FOREIGN KEY (category2_id) REFERENCES mercury_category2(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ジョブ管理
CREATE TABLE mercury_mapping_job (
    id INT PRIMARY KEY AUTO_INCREMENT,
    job_uuid VARCHAR(36) NOT NULL UNIQUE,
    category2_id INT UNSIGNED NOT NULL,
    company_a_id INT NOT NULL,
    company_b_id INT NOT NULL,
    file_a_path VARCHAR(500) NOT NULL,
    file_b_path VARCHAR(500) NOT NULL,
    result_url VARCHAR(500) NULL,
    local_result_path VARCHAR(500) NULL,
    mapping_options JSON,
    status ENUM('pending', 'running', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
    progress INT DEFAULT 0,
    total_records_a INT DEFAULT 0,
    total_records_b INT DEFAULT 0,
    matched_records INT DEFAULT 0,
    unmatched_records_a INT DEFAULT 0,
    unmatched_records_b INT DEFAULT 0,
    log_message TEXT,
    error_message TEXT,
    created_by VARCHAR(100),
    started_at DATETIME NULL,
    completed_at DATETIME NULL,
    active TINYINT(4) NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT NULL,
    updated_at DATETIME DEFAULT NULL,
    FOREIGN KEY (category2_id) REFERENCES mercury_category2(id),
    FOREIGN KEY (company_a_id) REFERENCES mercury_company(id),
    FOREIGN KEY (company_b_id) REFERENCES mercury_company(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 初期データ投入
INSERT INTO mercury_category2 (id, name, order_display, active, created_at) VALUES
(254, '名探偵コナンカードゲーム', 1, 1, NOW()),
(255, 'ポケモンカード', 2, 1, NOW()),
(256, '遊戯王', 3, 1, NOW());

INSERT INTO mercury_company (company_code, company_name, active, created_at) VALUES
('A', 'A社（Tay2）', 1, NOW()),
('B', 'B社（Youya）', 1, NOW());
