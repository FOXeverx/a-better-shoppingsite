-- Migration: Add new columns to user_profile table
-- Run this to update existing database

ALTER TABLE user_profile 
ADD COLUMN region VARCHAR(50) COMMENT 'User region' AFTER user_id,
ADD COLUMN total_spent DECIMAL(12, 2) DEFAULT 0 COMMENT 'Total amount spent' AFTER region,
ADD COLUMN order_count INT DEFAULT 0 COMMENT 'Total order count' AFTER total_spent,
ADD COLUMN avg_order_amount DECIMAL(12, 2) DEFAULT 0 COMMENT 'Average order amount' AFTER order_count,
ADD COLUMN preferred_categories JSON COMMENT 'Preferred product categories' AFTER avg_order_amount,
ADD COLUMN browse_category_stats JSON COMMENT 'Browse statistics by category' AFTER preferred_categories,
ADD COLUMN last_updated DATETIME COMMENT 'Last update timestamp' AFTER spending_level;

-- Create indexes
ALTER TABLE user_profile ADD INDEX idx_region (region);