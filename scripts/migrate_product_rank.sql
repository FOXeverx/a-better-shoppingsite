-- 修复 product_rank 唯一键：从 product_id 改为 (product_id, period)
-- 使得同一商品可以有 daily/weekly/monthly 三条排行记录

USE shopping_site;

-- 查找 product_rank 的外键约束名
SELECT CONSTRAINT_NAME INTO @fk
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'shopping_site'
  AND TABLE_NAME = 'product_rank'
  AND REFERENCED_TABLE_NAME IS NOT NULL
LIMIT 1;

-- 删除旧外键
SET @s = CONCAT('ALTER TABLE product_rank DROP FOREIGN KEY ', @fk);
PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 删除旧唯一索引，创建新的联合唯一索引
ALTER TABLE product_rank DROP INDEX product_id;
ALTER TABLE product_rank ADD UNIQUE KEY uk_product_period (product_id, period);

-- 恢复外键
ALTER TABLE product_rank ADD FOREIGN KEY (product_id) REFERENCES product(id);
