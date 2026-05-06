-- ============================================================
-- Shopping Site Pro - Database Initialization Script
-- MySQL 8.0+
-- ============================================================

-- Drop tables if exists (in correct order due to foreign keys)
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS recommend_item;
DROP TABLE IF EXISTS product_rank;
DROP TABLE IF EXISTS sales_stat;
DROP TABLE IF EXISTS anomaly_log;
DROP TABLE IF EXISTS user_profile;
DROP TABLE IF EXISTS operation_log;
DROP TABLE IF EXISTS browse_log;
DROP TABLE IF EXISTS login_log;
DROP TABLE IF EXISTS order_item;
DROP TABLE IF EXISTS `order`;
DROP TABLE IF EXISTS cart;
DROP TABLE IF EXISTS product;
DROP TABLE IF EXISTS category;
DROP TABLE IF EXISTS role;
DROP TABLE IF EXISTS user;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- 1. User and Role Tables
-- ============================================================

CREATE TABLE role (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE COMMENT 'Role name: customer, sales, admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='User roles';

CREATE TABLE user (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT 'Username for login',
    password_hash VARCHAR(255) NOT NULL COMMENT 'Bcrypt hashed password',
    email VARCHAR(100) NOT NULL UNIQUE COMMENT 'User email',
    role_id INT NOT NULL DEFAULT 1 COMMENT 'FK to role table',
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Account active status',
    last_login_at DATETIME COMMENT 'Last login timestamp',
    login_attempts INT DEFAULT 0 COMMENT 'Failed login attempts count',
    blocked_until DATETIME COMMENT 'Account blocked until',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES role(id) ON DELETE RESTRICT,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role_id (role_id),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='User accounts';

-- ============================================================
-- 2. Product and Category Tables
-- ============================================================

CREATE TABLE category (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE COMMENT 'Category name',
    parent_id INT NULL COMMENT 'Parent category for subcategories',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES category(id) ON DELETE SET NULL,
    INDEX idx_parent_id (parent_id),
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Product categories';

CREATE TABLE product (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL COMMENT 'Product name',
    description TEXT COMMENT 'Product description',
    price DECIMAL(10, 2) NOT NULL COMMENT 'Product price',
    stock INT NOT NULL DEFAULT 0 COMMENT 'Available stock quantity',
    category_id INT COMMENT 'FK to category table',
    image_url VARCHAR(500) COMMENT 'Product image URL',
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Product active status',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE SET NULL,
    INDEX idx_name (name),
    INDEX idx_category_id (category_id),
    INDEX idx_price (price),
    INDEX idx_is_active (is_active),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Products';

-- ============================================================
-- 3. Cart Table
-- ============================================================

CREATE TABLE cart (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT 'FK to user table',
    product_id INT NOT NULL COMMENT 'FK to product table',
    quantity INT NOT NULL DEFAULT 1 COMMENT 'Quantity in cart',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_product (user_id, product_id),
    INDEX idx_user_id (user_id),
    INDEX idx_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Shopping cart';

-- ============================================================
-- 4. Order Tables
-- ============================================================

CREATE TABLE `order` (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT 'FK to user table',
    status ENUM('CREATED', 'CONFIRMED', 'CANCELLED') NOT NULL DEFAULT 'CREATED' COMMENT 'Order status',
    total_amount DECIMAL(10, 2) NOT NULL COMMENT 'Total order amount',
    confirm_token VARCHAR(255) NULL UNIQUE COMMENT 'Email confirmation token',
    confirmed_at DATETIME COMMENT 'Order confirmed timestamp',
    expires_at DATETIME NOT NULL COMMENT 'Order expiration timestamp',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE RESTRICT,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_confirm_token (confirm_token),
    INDEX idx_expires_at (expires_at),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Orders';

CREATE TABLE order_item (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL COMMENT 'FK to order table',
    product_id INT NOT NULL COMMENT 'FK to product table',
    quantity INT NOT NULL COMMENT 'Item quantity',
    price DECIMAL(10, 2) NOT NULL COMMENT 'Price at time of order',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES `order`(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE RESTRICT,
    INDEX idx_order_id (order_id),
    INDEX idx_product_id (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Order items';

-- ============================================================
-- 5. Login Log Table
-- ============================================================

CREATE TABLE login_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT COMMENT 'FK to user table (nullable for failed attempts)',
    username VARCHAR(50) NOT NULL COMMENT 'Username attempted',
    ip_address VARCHAR(45) NOT NULL COMMENT 'Client IP address',
    user_agent VARCHAR(500) COMMENT 'Client user agent',
    success BOOLEAN NOT NULL COMMENT 'Login success status',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_username (username),
    INDEX idx_ip_address (ip_address),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Login logging';

-- ============================================================
-- 6. Browse Log Table
-- ============================================================

CREATE TABLE browse_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT 'FK to user table',
    product_id INT NOT NULL COMMENT 'FK to product table',
    stay_time INT NOT NULL DEFAULT 0 COMMENT 'Stay time in seconds',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_product_id (product_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Product browse logging';

-- ============================================================
-- 7. Operation Log Table
-- ============================================================

CREATE TABLE operation_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT 'FK to user table',
    action VARCHAR(100) NOT NULL COMMENT 'Operation action',
    target_type VARCHAR(50) COMMENT 'Target entity type',
    target_id INT COMMENT 'Target entity ID',
    details TEXT COMMENT 'Operation details',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_target (target_type, target_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Operation logging';

-- ============================================================
-- 8. User Profile Table
-- ============================================================

CREATE TABLE user_profile (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE COMMENT 'FK to user table',
    region VARCHAR(50) COMMENT 'User region',
    total_spent DECIMAL(12, 2) DEFAULT 0 COMMENT 'Total amount spent',
    order_count INT DEFAULT 0 COMMENT 'Total order count',
    avg_order_amount DECIMAL(12, 2) DEFAULT 0 COMMENT 'Average order amount',
    preferred_categories JSON COMMENT 'Preferred product categories',
    browse_category_stats JSON COMMENT 'Browse statistics by category',
    spending_level ENUM('low', 'medium', 'high') DEFAULT 'low' COMMENT 'Spending level',
    last_updated DATETIME COMMENT 'Last update timestamp',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_spending_level (spending_level),
    INDEX idx_region (region)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='User profiles for analytics';

-- ============================================================
-- 9. Sales Stat Table
-- ============================================================

CREATE TABLE sales_stat (
    id INT PRIMARY KEY AUTO_INCREMENT,
    stat_date DATE NOT NULL UNIQUE COMMENT 'Statistics date',
    total_amount DECIMAL(12, 2) DEFAULT 0 COMMENT 'Total sales amount',
    order_count INT DEFAULT 0 COMMENT 'Total order count',
    user_count INT DEFAULT 0 COMMENT 'Unique buyer count',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_stat_date (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Sales statistics';

-- ============================================================
-- 10. Product Rank Table
-- ============================================================

CREATE TABLE product_rank (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL UNIQUE COMMENT 'FK to product table',
    rank_score DECIMAL(10, 2) DEFAULT 0 COMMENT 'Rank score',
    rank_position INT COMMENT 'Current rank position',
    period ENUM('daily', 'weekly', 'monthly') DEFAULT 'daily' COMMENT 'Ranking period',
    last_analysis_at DATETIME COMMENT 'Last analysis timestamp',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE,
    INDEX idx_rank_position (rank_position),
    INDEX idx_period (period)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Product rankings';

-- ============================================================
-- 11. Anomaly Log Table
-- ============================================================

CREATE TABLE anomaly_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    anomaly_type VARCHAR(100) NOT NULL COMMENT 'Anomaly type',
    description TEXT NOT NULL COMMENT 'Anomaly description',
    severity ENUM('low', 'medium', 'high') DEFAULT 'medium' COMMENT 'Anomaly severity',
    details JSON COMMENT 'Additional details',
    is_resolved BOOLEAN DEFAULT FALSE COMMENT 'Resolution status',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME COMMENT 'Resolution timestamp',
    INDEX idx_anomaly_type (anomaly_type),
    INDEX idx_severity (severity),
    INDEX idx_is_resolved (is_resolved),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Anomaly detection logging';

-- ============================================================
-- 12. Recommend Item Table
-- ============================================================

CREATE TABLE recommend_item (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL COMMENT 'Source product ID',
    recommend_product_id INT NOT NULL COMMENT 'Recommended product ID',
    score DECIMAL(5, 4) NOT NULL DEFAULT 0 COMMENT 'Recommendation score',
    algorithm VARCHAR(50) NOT NULL DEFAULT 'cooccurrence' COMMENT 'Algorithm used',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_product_recommend (product_id, recommend_product_id),
    INDEX idx_product_id (product_id),
    INDEX idx_score (score),
    INDEX idx_algorithm (algorithm)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Product recommendations';

-- ============================================================
-- Insert Default Roles
-- ============================================================

INSERT INTO role (name) VALUES ('customer'), ('sales'), ('admin');

-- ============================================================
-- Create Views for Analytics
-- ============================================================

CREATE OR REPLACE VIEW v_user_stats AS
SELECT 
    DATE(created_at) AS date,
    COUNT(*) AS new_users,
    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS active_users
FROM user
GROUP BY DATE(created_at);

CREATE OR REPLACE VIEW v_order_stats AS
SELECT 
    DATE(created_at) AS date,
    COUNT(*) AS order_count,
    SUM(CASE WHEN status = 'CONFIRMED' THEN 1 ELSE 0 END) AS confirmed_count,
    SUM(CASE WHEN status = 'CONFIRMED' THEN total_amount ELSE 0 END) AS total_amount
FROM `order`
GROUP BY DATE(created_at);