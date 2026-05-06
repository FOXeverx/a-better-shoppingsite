# 系统优化建议

## 一、性能优化

### 1.1 数据库优化

#### 索引优化

```sql
-- 复合索引示例
CREATE INDEX idx_product_category_price ON product(category_id, price);
CREATE INDEX idx_order_user_status ON `order`(user_id, status);

-- 覆盖索引（包含额外列避免回表）
CREATE INDEX idx_order_cover ON `order`(id, user_id, status, total_amount);
```

#### 查询优化

- 使用EXPLAIN分析慢查询
- 避免SELECT *
- 使用LIMIT分页
- 批量操作使用INSERT...VALUES(),(),()

#### 连接池配置

```python
# app/model/database.py
engine = create_engine(
    config.database.url,
    pool_size=20,           # 默认连接数
    max_overflow=30,         # 最大溢出
    pool_recycle=3600,        # 连接回收时间
    pool_pre_ping=True       # 连接检测
)
```

### 1.2 缓存策略

#### Redis缓存（推荐）

```python
# 安装: pip install redis
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_key(*args, **kwargs):
    return f"{args}:{kwargs}"

def cached(expire=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{cache_key(*args, **kwargs)}"
            cached_result = redis_client.get(key)
            if cached_result:
                return json.loads(cached_result)
            result = func(*args, **kwargs)
            redis_client.setex(key, expire, json.dumps(result))
            return result
        return wrapper
    return decorator
```

#### 缓存热点数据

- 商品分类（ infrequent变化）
- 系统配置
- 用户角色权限

### 1.3 API优化

#### 分页优化

```python
# 后端游标分页（更高效）
@router.get("/products")
async def get_products(cursor: int = None, limit: int = 20):
    query = db.query(Product)
    if cursor:
        query = query.filter(Product.id > cursor)
    products = query.limit(limit).all()
    return products
```

#### 压缩响应

```python
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000
)
```

---

## 二、并发优化

### 2.1 订单并发控制

#### 行级锁

```python
# 使用FOR UPDATE
product = db.query(Product).filter(
    Product.id == product_id
).with_for_update().first()

# 事务隔离级别
from sqlalchemy import event

@event.listens_for(engine, "connect")
def set_serializable(dbapi_conn, connection_record):
    dbapi_conn.isolation_level = "SERIALIZABLE"
```

#### 库存锁优化（当前使用悲观锁，创建订单时扣库存）

当前库存扣减已提前至订单创建阶段（`create_order()`），使用 `SELECT ... FOR UPDATE` 悲观锁确保并发安全。如需进一步优化，可考虑乐观锁方案：

```sql
ALTER TABLE product ADD COLUMN version INT DEFAULT 0;

-- 更新时检查版本
UPDATE product 
SET stock = stock - 1, version = version + 1 
WHERE id = ? AND stock > 0 AND version = ?;
```

#### 消息队列（订单异步处理）

```python
# 安装: pip install pika
import pika

def publish_order(order_id):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost')
    )
    channel = connection.channel()
    channel.queue_declare(queue='orders')
    channel.basic_publish(
        exchange='',
        routing_key='orders',
        body=str(order_id)
    )
```

### 2.2 限流优化

#### 分布式限流（Redis）

```python
def rate_limit(key: str, limit: int, window: int = 60) -> bool:
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, window)
    return current <= limit
```

---

## 三、架构优化

### 3.1 服务拆分

```
api-gateway/          # 网关服务
├── auth-service/     # 认证服务
├── product-service/  # 商品服务
├── order-service/    # 订单服务
└── recommend-service/ # 推荐服务
```

### 3.2 读写分离

```python
# 主库（写）
master_engine = create_engine(master_url)

# 从库（读）
replica_engine = create_engine(replica_url)

def get_db(role='master'):
    if role == 'replica':
        return replica_engine
    return master_engine
```

### 3.3 日志异步写入

```python
# 使用queue异步写日志
import queue
import threading

log_queue = queue.Queue()

def async_logger():
    while True:
        log_entry = log_queue.get()
        # 写入数据库
        save_log(log_entry)

logging_thread = threading.Thread(target=async_logger, daemon=True)
logging_thread.start()
```

---

## 四、安全增强

### 4.1 接口签名验证

```python
import hmac
import hashlib

def verify_signature(secret: str, data: str, signature: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### 4.2 请求去重（幂等）

```python
import uuid

def idempotency_key(key: str) -> bool:
    exists = redis_client.exists(f"idempotent:{key}")
    if exists:
        return False
    redis_client.setex(f"idempotent:{key}", 3600, "1")
    return True
```

### 4.3 敏感数据加密

```python
# 使用cryptography库
from cryptography.fernet import Fernet

cipher = Fernet(key)

def encrypt(data: str) -> str:
    return cipher.encrypt(data.encode()).decode()

def decrypt(data: str) -> str:
    return cipher.decrypt(data.encode()).decode()
```

---

## 五、监控与告警

### 5.1 性能监控

```python
# 使用sentry
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=0.1
)
```

### 5.2 业务指标

```python
# 使用prometheus
from prometheus_client import Counter, Histogram

order_created_total = Counter(
    'order_created_total',
    'Total orders created'
)

request_duration = Histogram(
    'request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)
```

---

## 六、部署建议

### 6.1 Docker化

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

### 6.2 Nginx配置

```nginx
upstream api {
    server localhost:8000;
}

server {
    location /api/ {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        proxy_pass http://localhost:3000;
    }
}
```

---

## 七、优化总结表

| 优化项 | 实施难度 | 效果 | 优先级 |
|--------|----------|------|--------|
| 添加索引 | 低 | 高 | P0 |
| 连接池 | 低 | 高 | P0 |
| Redis缓存 | 中 | 高 | P0 |
| 读写分离 | 中 | 高 | P1 |
| 消息队列 | 中 | 高 | P1 |
| 服务拆分 | 高 | 高 | P2 |
| 微服务 | 高 | 高 | P2 |